# Blog API with File Upload

A full-stack blog application built with FastAPI (backend) and vanilla JavaScript (frontend). Features include post creation, image uploads, tagging, search, pagination, and statistics.

## Features

### Backend
- ✅ RESTful API with FastAPI
- ✅ CRUD operations for blog posts
- ✅ Image upload functionality
- ✅ Comment system
- ✅ Tag management
- ✅ Search and filtering
- ✅ Pagination support
- ✅ Statistics dashboard
- ✅ CORS enabled for frontend integration

### Frontend
- ✅ Clean, modern UI
- ✅ Create and manage blog posts
- ✅ Upload images for posts
- ✅ Search posts by title/content
- ✅ Real-time statistics
- ✅ Responsive design
- ✅ Pagination controls

## Tech Stack

**Backend:**
- FastAPI 
- Python 
- Pydantic for data validation
- Uvicorn ASGI server

**Frontend:**
- HTML5
- CSS3 (with gradients and modern styling)
- Vanilla JavaScript (ES6+)
- Fetch API for HTTP requests

## Installation

### Prerequisites
- Python 
- pip (Python package manager)

### Backend Setup

1. Clone the repository:
```bash
git clone https://github.com/AtharvaDomale/Blog-API-with-File-Upload---Full-Stack-Project.git


## API Endpoints

### Posts

- `POST /posts` — Create a new post  
- `GET /posts` — Get all posts (with pagination, search, filters)  
- `GET /posts/{post_id}` — Get a specific post  
- `PUT /posts/{post_id}` — Update a post  
- `DELETE /posts/{post_id}` — Delete a post  
- `POST /posts/{post_id}/image` — Upload image for a post  

### Comments

- `POST /posts/{post_id}/comments` — Add a comment to a post  
- `GET /posts/{post_id}/comments` — Get all comments for a post  
- `DELETE /comments/{comment_id}` — Delete a comment  

### Tags

- `GET /tags` — Get all tags  
- `GET /tags/{tag_name}/posts` — Get all posts with a specific tag  

### Statistics

- `GET /stats` — Get blog statistics

