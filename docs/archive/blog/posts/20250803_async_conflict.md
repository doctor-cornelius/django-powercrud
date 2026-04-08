---
date: 2025-08-03
categories:
  - django
  - async
  - bulk
---
# Django Async Task Conflict Prevention for PowerCRUD

By introducing async processing we introduce potential conflicts. Also want to allow downstream project developers to use the same base mechanism for conflict detection, in case they want to run async processes independent of `powercrud` (eg `save()` method that updates child and descendant objects) but want overall conflict detection.

## Problems to Solve

1. **Lock conflicts** - preventing simultaneous updates to same objects
2. **User state confusion** - users making decisions based on stale data while async tasks are running
3. **Race conditions** - timing-dependent bugs in concurrent operations
4. **Complex dependencies** - bulk operations, single saves with descendant updates, and async tasks can all affect overlapping sets of objects
5. **Downstream flexibility** - powercrud needs to work with any downstream project's specific object relationships

<!-- more -->

## Strategic Approaches Considered

**Option 1: Lock Hierarchies** When you lock an object, you also lock its entire descendant tree. Simple but potentially over-restrictive.

**Option 2: Dependency Mapping** Before starting any operation, compute ALL affected objects (including descendants), then lock that entire set.

**Option 3: Lock Inheritance** Objects "inherit" locks from their parents. If parent is locked, all descendants are implicitly locked too.

**Option 4: Transaction Queuing** Don't try to prevent conflicts - instead queue conflicting operations to run after the current one finishes.

## Key Insight

We can **compute the full set of affected objects upfront** before starting any operation, which greatly simplifies the solution. This led us to choose **Option 2: Dependency Mapping**.

## Recommended Solution - Preemptive locking with method override pattern

1. **Dependency Resolution Hook**: Add `get_dependent_objects(object_ids)` method to PowerCRUDMixin that downstream devs can override
2. **Before any operation**: Call the hook to compute ALL affected object IDs (including downstream-specific descendants)
3. **Lock the entire set atomically** - either get all locks or fail/queue
4. **Use Redis sets** for fast atomic operations when available, fall back to database table when not
5. **Auto-detect backend** - check if Redis is configured, gracefully fall back to database locking
6. **Release locks** when operation completes (success or failure)

### Package Configuration

```python
POWERCRUD_ASYNC_CONFLICT_PREVENTION = True  
POWERCRUD_LOCKING_BACKEND = 'auto'  # auto-detect Redis, fallback to DB
```

### Downstream Developer API

Not sure if this will always work, but worth examining as a starting point.

```python
class ProjectCRUDView(PowerCRUDMixin, CRUDView):
    model = models.Project
   
    def get_dependent_objects(self, object_ids):
        """Override to specify all objects affected by operations"""
        affected = {'Project': list(object_ids)}  # Include self
       
        # Add your specific dependencies
        for obj_id in object_ids:
            children = get_children_ids(obj_id)
            affected.setdefault('ChildModel', []).extend(children)
           
        return affected
```

### Lock Storage Implementation

**Redis approach (preferred) - Model-specific sets:**

For 10 RespondentAssetType IDs being locked:

```
Redis key: "locked:RespondentAssetType"
Set members: ["101", "102", "103", "104", "105", "106", "107", "108", "109", "110"]

Redis key: "locked:Project" 
Set members: ["25", "47"]

Redis key: "locked:ChildModel"
Set members: ["88", "92", "156", "203"]
```

- Key Redis commands: `SADD` (add locks), `SISMEMBER` (check locks), `SREM` (remove locks)
- Lock format: Store just the object IDs in each model's set
- Benefits: Cleaner organization, easier to debug per-model, efficient queries

**Database fallback:**

```python
class ObjectLock(models.Model):
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    operation_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
   
    class Meta:
        unique_together = ['model_name', 'object_id']
```

This approach provides `powercrud` with conflict prevention while allowing downstream projects to define their specific object dependencies through a clean override pattern that fits the existing architecture.