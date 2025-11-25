# AGENTS.md file for the django-powercrud repo

## Tips when writing docs
- we use Material for Mkdocs format
- when indenting is required, use 4 spaces
- put linefeed before the start of any list
- put linefeed before the start of any code fences

## When working on blog articles for planning
- the user will often use the blog feature to write articles as the basis for planning and controlling focused work.  
- user will run `newblog.sh` to create a new article and will then instruct you
- for the tasks part, put `[ ]` in each task and subtask. The user will instruct you when to change these to `[X]`

## Running in user's terminal
- unless specifically instructed you are never to run commands other than to edit source code or run tests
- when running tests recognise that the user may prefer to run tests themselves, although you can ask them if you can run them. 
- Check `runtests` bash script to understand how tests are configured
- realise that the user works in the django dockerised container which you do not have access to. Their native WSL environment is not the dev env for this repo.