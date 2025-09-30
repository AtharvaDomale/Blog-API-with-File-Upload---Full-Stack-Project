from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import shutil
import os
from pathlib import Path
import uuid

app = FastAPI(title="Blog API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for uploads
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# In-memory databases
posts_db = {}
comments_db = {}
tags_db = set()
post_counter = 0
comment_counter = 0

# Models
class Tag(BaseModel):
    name: str

class PostBase(BaseModel):
    title: str
    content: str
    tags: List[str] = []
    published: bool = False
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v

class PostCreate(PostBase):
    pass

class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    published: Optional[bool] = None

class Post(PostBase):
    id: int
    author: str
    image_url: Optional[str] = None
    views: int
    created_at: datetime
    updated_at: datetime

class PaginatedPosts(BaseModel):
    items: List[Post]
    total: int
    page: int
    page_size: int
    total_pages: int

class CommentBase(BaseModel):
    content: str
    author: str

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    post_id: int
    created_at: datetime

class PostStats(BaseModel):
    total_posts: int
    published_posts: int
    draft_posts: int
    total_views: int
    total_comments: int
    popular_tags: List[dict]

# Helper functions
def get_post_or_404(post_id: int):
    post = posts_db.get(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

def increment_views(post_id: int):
    if post_id in posts_db:
        posts_db[post_id]["views"] += 1

def calculate_pagination(total: int, page: int, page_size: int):
    total_pages = (total + page_size - 1) // page_size
    return total_pages

# Routes
@app.get("/")
async def root():
    return {
        "message": "Welcome to Blog API",
        "endpoints": {
            "posts": "/posts",
            "tags": "/tags",
            "stats": "/stats"
        }
    }

@app.post("/posts", response_model=Post, status_code=201)
async def create_post(post: PostCreate, author: str = Query(..., min_length=3)):
    global post_counter
    post_counter += 1
    now = datetime.utcnow()
    
    for tag in post.tags:
        tags_db.add(tag.lower())
    
    post_data = {
        "id": post_counter,
        "author": author,
        "image_url": None,
        "views": 0,
        "created_at": now,
        "updated_at": now,
        **post.dict()
    }
    posts_db[post_counter] = post_data
    return Post(**post_data)

@app.post("/posts/{post_id}/image")
async def upload_post_image(post_id: int, file: UploadFile = File(...)):
    post = get_post_or_404(post_id)
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    post["image_url"] = f"/uploads/{unique_filename}"
    post["updated_at"] = datetime.utcnow()
    
    return {"message": "Image uploaded successfully", "image_url": post["image_url"]}

@app.get("/posts", response_model=PaginatedPosts)
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    published: Optional[bool] = None,
    search: Optional[str] = None
):
    filtered_posts = list(posts_db.values())
    
    if tag:
        filtered_posts = [p for p in filtered_posts if tag.lower() in [t.lower() for t in p["tags"]]]
    
    if published is not None:
        filtered_posts = [p for p in filtered_posts if p["published"] == published]
    
    if search:
        search_lower = search.lower()
        filtered_posts = [
            p for p in filtered_posts 
            if search_lower in p["title"].lower() or search_lower in p["content"].lower()
        ]
    
    filtered_posts.sort(key=lambda x: x["created_at"], reverse=True)
    
    total = len(filtered_posts)
    total_pages = calculate_pagination(total, page, page_size)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_posts = filtered_posts[start:end]
    
    return PaginatedPosts(
        items=[Post(**p) for p in paginated_posts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: int):
    post = get_post_or_404(post_id)
    increment_views(post_id)
    return Post(**post)

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: int, post_update: PostUpdate):
    post = get_post_or_404(post_id)
    
    update_data = post_update.dict(exclude_unset=True)
    
    if "tags" in update_data:
        for tag in update_data["tags"]:
            tags_db.add(tag.lower())
    
    for field, value in update_data.items():
        post[field] = value
    
    post["updated_at"] = datetime.utcnow()
    return Post(**post)

@app.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int):
    post = get_post_or_404(post_id)
    
    if post.get("image_url"):
        image_path = UPLOAD_DIR / post["image_url"].split("/")[-1]
        if image_path.exists():
            image_path.unlink()
    
    comments_to_delete = [cid for cid, c in comments_db.items() if c["post_id"] == post_id]
    for cid in comments_to_delete:
        del comments_db[cid]
    
    del posts_db[post_id]
    return None

@app.post("/posts/{post_id}/comments", response_model=Comment, status_code=201)
async def create_comment(post_id: int, comment: CommentCreate):
    get_post_or_404(post_id)
    
    global comment_counter
    comment_counter += 1
    
    comment_data = {
        "id": comment_counter,
        "post_id": post_id,
        "created_at": datetime.utcnow(),
        **comment.dict()
    }
    comments_db[comment_counter] = comment_data
    return Comment(**comment_data)

@app.get("/posts/{post_id}/comments", response_model=List[Comment])
async def get_comments(post_id: int):
    get_post_or_404(post_id)
    post_comments = [c for c in comments_db.values() if c["post_id"] == post_id]
    post_comments.sort(key=lambda x: x["created_at"], reverse=True)
    return [Comment(**c) for c in post_comments]

@app.delete("/comments/{comment_id}", status_code=204)
async def delete_comment(comment_id: int):
    if comment_id not in comments_db:
        raise HTTPException(status_code=404, detail="Comment not found")
    del comments_db[comment_id]
    return None

@app.get("/tags", response_model=List[str])
async def get_tags():
    return sorted(list(tags_db))

@app.get("/tags/{tag_name}/posts", response_model=List[Post])
async def get_posts_by_tag(tag_name: str):
    tag_posts = [
        p for p in posts_db.values() 
        if tag_name.lower() in [t.lower() for t in p["tags"]]
    ]
    tag_posts.sort(key=lambda x: x["created_at"], reverse=True)
    return [Post(**p) for p in tag_posts]

@app.get("/stats", response_model=PostStats)
async def get_stats():
    all_posts = list(posts_db.values())
    published = [p for p in all_posts if p["published"]]
    drafts = [p for p in all_posts if not p["published"]]
    total_views = sum(p["views"] for p in all_posts)
    
    tag_counts = {}
    for post in all_posts:
        for tag in post["tags"]:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    popular_tags = [
        {"tag": tag, "count": count} 
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]
    
    return PostStats(
        total_posts=len(all_posts),
        published_posts=len(published),
        draft_posts=len(drafts),
        total_views=total_views,
        total_comments=len(comments_db),
        popular_tags=popular_tags
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)