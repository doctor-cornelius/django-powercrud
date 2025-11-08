f# Django powercrud - Project Description

## Overview
Django powercrud is an opinionated extension package for the excellent `neapolitan` Django package, designed to enhance CRUD (Create, Read, Update, Delete) operations with advanced features and modern web technologies.

## Main Objectives
- Extend neapolitan's capabilities with production-ready features
- Provide seamless HTMX integration for reactive web interfaces
- Offer comprehensive filtering, bulk operations, and modal support
- Enable flexible template customization and CSS framework integration

## Key Features
- **Advanced CRUD Operations**: Enhanced list/detail views with property support and field exclusions
- **Inline Editing**: Row-level editing without breaking context, with HTMX-powered reactive updates
- **HTMX Integration**: Reactive pagination, modal dialogs, and partial page updates
- **Filtering & Search**: Comprehensive filterset support with M2M logic and custom queryset options
- **Bulk Operations**: Multi-record editing and deletion with atomic transactions and async processing
- **Async Processing**: django-q2 support for handling large bulk operations with progress tracking and conflict management
- **Async Dashboard**: Lifecycle event persistence and monitoring for background tasks
- **Template System**: Flexible template overrides with DaisyUI and Bootstrap5 support and potential extension to other css frameworks
- **Form Enhancement**: Crispy-forms integration with HTML5 widgets
- **Table Features**: Sortable columns, pagination, and responsive design
- **Management Commands**: Template bootstrapping and Tailwind CSS class extraction

## Technologies Used
- **Backend**: Django, Neapolitan, Pydantic
- **Frontend**: HTMX, Alpine.js, DaisyUI
- **Forms**: Django Crispy Forms
- **Styling**: Tailwind CSS, Bootstrap Icons
- **JavaScript**: Popper.js for enhanced UI interactions

## Significance
This package bridges the gap between Django's basic CRUD functionality and modern web application requirements, providing developers with a comprehensive toolkit for building responsive, feature-rich admin interfaces and data management systems without extensive custom development.

## Status
Early alpha release - expect breaking changes. Suitable for experimentation and development environments.
