-- init.sql
-- 1. 啟用 pgvector 擴充套件
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 建立 documents 資料表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL -- 假設使用 1536 維的向量
);