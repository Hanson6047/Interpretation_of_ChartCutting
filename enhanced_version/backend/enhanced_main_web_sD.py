#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
階段D：增強版Web API - 支援圖文混合問答展示
"""

import os
import asyncio
import hashlib
import jwt
import json
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import uuid
from contextlib import asynccontextmanager

# 導入增強型RAG系統
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.pdf_Cutting_TextReplaceImage.enhanced_version.backend.enhanced_rag_helper_sC import EnhancedRAGHelper, ChartMetadata

# 載入環境變數
load_dotenv()

# 安全設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 資料庫初始化
def init_database():
    """初始化 SQLite 資料庫"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()

    # 使用者表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        is_active BOOLEAN DEFAULT TRUE,
        is_admin BOOLEAN DEFAULT FALSE
    )
    ''')

    # 增強的問答紀錄表（新增圖表欄位）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enhanced_questions_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        sources_count INTEGER DEFAULT 0,
        charts_count INTEGER DEFAULT 0,
        chart_references TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        response_time REAL,
        FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')

    conn.commit()
    conn.close()

# 應用程式生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    init_database()
    yield
    # 關閉時執行（如果需要清理）

# FastAPI 應用程式
app = FastAPI(
    title="增強型RAG問答系統",
    description="支援圖文混合的智能問答系統",
    lifespan=lifespan
)

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全域增強型RAG實例
enhanced_rag_instance: Optional[EnhancedRAGHelper] = None

# 安全相關
security = HTTPBearer()

# 資料模型
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class QuestionRequest(BaseModel):
    question: str

class EnhancedQuestionResponse(BaseModel):
    """增強的問答回應 - 包含圖表資訊"""
    answer: str
    sources: List[Dict[str, Any]]
    charts: List[Dict[str, Any]]
    response_time: float
    charts_count: int
    sources_count: int

# 工具函數
def hash_password(password: str) -> str:
    """密碼雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """驗證密碼"""
    return hash_password(password) == hashed

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """建立 JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """驗證 JWT token"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_from_db(user_id: str):
    """從資料庫取得使用者資訊"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def chart_metadata_to_dict(chart: ChartMetadata) -> Dict[str, Any]:
    """將圖表元數據轉換為字典"""
    return {
        "chart_id": chart.chart_id,
        "chart_type": chart.chart_type,
        "chart_number": chart.chart_number,
        "original_caption": chart.original_caption,
        "generated_description": chart.generated_description,
        "page_number": chart.page_number,
        "confidence_score": chart.confidence_score,
        "source_file": chart.source_file
    }

# API 路由
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """主頁"""
    return FileResponse("../frontend/enhanced_index.html")

@app.post("/register")
async def register(user: UserCreate):
    """使用者註冊"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()
    
    try:
        # 檢查使用者名稱是否已存在
        cursor.execute("SELECT username FROM users WHERE username = ?", (user.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="使用者名稱已存在")
        
        # 建立新使用者
        user_id = str(uuid.uuid4())
        password_hash = hash_password(user.password)
        
        cursor.execute("""
            INSERT INTO users (user_id, username, email, password_hash) 
            VALUES (?, ?, ?, ?)
        """, (user_id, user.username, user.email, password_hash))
        
        conn.commit()
        return {"message": "註冊成功", "user_id": user_id}
    
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="使用者名稱已存在")
    finally:
        conn.close()

@app.post("/login")
async def login(user: UserLogin):
    """使用者登入"""
    conn = sqlite3.connect('rag_users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (user.username,))
    db_user = cursor.fetchone()
    conn.close()
    
    if not db_user or not verify_password(user.password, db_user[1]):
        raise HTTPException(status_code=401, detail="帳號或密碼錯誤")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user[0]}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/init-rag")
async def init_rag(user_id: str = Depends(verify_token)):
    """初始化增強型RAG系統"""
    global enhanced_rag_instance
    
    try:
        if enhanced_rag_instance is None:
            enhanced_rag_instance = EnhancedRAGHelper("pdfFiles")
            await asyncio.get_event_loop().run_in_executor(
                None, enhanced_rag_instance.load_and_prepare_enhanced, False
            )
            enhanced_rag_instance.setup_enhanced_retrieval_chain()
        
        # 獲取系統統計
        stats = enhanced_rag_instance.get_statistics()
        
        return {
            "message": "增強型RAG系統初始化完成",
            "statistics": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失敗: {str(e)}")

@app.post("/ask", response_model=EnhancedQuestionResponse)
async def ask_question(request: QuestionRequest, user_id: str = Depends(verify_token)):
    """增強型問答"""
    global enhanced_rag_instance
    
    if enhanced_rag_instance is None:
        raise HTTPException(status_code=400, detail="RAG系統尚未初始化，請先呼叫 /init-rag")
    
    start_time = datetime.now()
    
    try:
        # 執行增強型問答
        answer, context_docs, related_charts = await asyncio.get_event_loop().run_in_executor(
            None, enhanced_rag_instance.ask_enhanced, request.question
        )
        
        # 處理回應時間
        response_time = (datetime.now() - start_time).total_seconds()
        
        # 準備來源文檔資訊
        sources = []
        for doc in context_docs:
            sources.append({
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "metadata": doc.metadata
            })
        
        # 準備圖表資訊
        charts = [chart_metadata_to_dict(chart) for chart in related_charts]
        
        # 記錄到資料庫
        conn = sqlite3.connect('rag_users.db')
        cursor = conn.cursor()
        
        chart_references_json = json.dumps([chart.chart_id for chart in related_charts])
        
        cursor.execute("""
            INSERT INTO enhanced_questions_log 
            (user_id, question, answer, sources_count, charts_count, chart_references, response_time) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, request.question, answer, len(sources), len(charts), chart_references_json, response_time))
        
        conn.commit()
        conn.close()
        
        return EnhancedQuestionResponse(
            answer=answer,
            sources=sources,
            charts=charts,
            response_time=response_time,
            charts_count=len(charts),
            sources_count=len(sources)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"問答處理失敗: {str(e)}")

@app.get("/charts")
async def list_charts(user_id: str = Depends(verify_token)):
    """列出所有圖表"""
    global enhanced_rag_instance
    
    if enhanced_rag_instance is None:
        raise HTTPException(status_code=400, detail="RAG系統尚未初始化")
    
    try:
        charts = enhanced_rag_instance.list_all_charts()
        return {
            "total_charts": len(charts),
            "charts": [chart_metadata_to_dict(chart) for chart in charts]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取圖表列表失敗: {str(e)}")

@app.get("/charts/{chart_id}")
async def get_chart(chart_id: str, user_id: str = Depends(verify_token)):
    """獲取特定圖表詳情"""
    global enhanced_rag_instance
    
    if enhanced_rag_instance is None:
        raise HTTPException(status_code=400, detail="RAG系統尚未初始化")
    
    chart = enhanced_rag_instance.get_chart_by_id(chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="圖表不存在")
    
    return chart_metadata_to_dict(chart)

@app.get("/statistics")
async def get_statistics(user_id: str = Depends(verify_token)):
    """獲取系統統計資訊"""
    global enhanced_rag_instance
    
    if enhanced_rag_instance is None:
        raise HTTPException(status_code=400, detail="RAG系統尚未初始化")
    
    try:
        # RAG系統統計
        rag_stats = enhanced_rag_instance.get_statistics()
        
        # 問答紀錄統計
        conn = sqlite3.connect('rag_users.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_questions_log")
        total_questions = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(response_time) FROM enhanced_questions_log")
        avg_response_time = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(charts_count) FROM enhanced_questions_log")
        total_chart_references = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "rag_statistics": rag_stats,
            "usage_statistics": {
                "total_questions": total_questions,
                "average_response_time": round(avg_response_time, 2),
                "total_chart_references": total_chart_references
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取統計資訊失敗: {str(e)}")

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_initialized": enhanced_rag_instance is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)