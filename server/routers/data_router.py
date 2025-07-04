import os
import asyncio
import traceback
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Body, Form, Query

from src.utils import logger, hashstr
from src import executor, retriever, config, knowledge_base, graph_base
from server.utils.auth_middleware import get_admin_user
from server.models.user_model import User

data = APIRouter(prefix="/data")


@data.get("/")
async def get_databases(current_user: User = Depends(get_admin_user)):
    try:
        database = knowledge_base.get_databases()
    except Exception as e:
        logger.error(f"获取数据库列表失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取数据库列表失败 {e}", "databases": []}
    return database

@data.post("/")
async def create_database(
    database_name: str = Body(...),
    description: str = Body(...),
    dimension: int | None = Body(None),
    current_user: User = Depends(get_admin_user)
):
    logger.debug(f"Create database {database_name}")
    try:
        database_info = knowledge_base.create_database(
            database_name,
            description,
            dimension=dimension
        )
    except Exception as e:
        logger.error(f"创建数据库失败 {e}, {traceback.format_exc()}")
        return {"message": f"创建数据库失败 {e}", "status": "failed"}
    return database_info

@data.delete("/")
async def delete_database(db_id, current_user: User = Depends(get_admin_user)):
    logger.debug(f"Delete database {db_id}")
    knowledge_base.delete_database(db_id)
    return {"message": "删除成功"}

@data.post("/query-test")
async def query_test(query: str = Body(...), meta: dict = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"Query test in {meta}: {query}")
    result = retriever.query_knowledgebase(query, history=None, refs={"meta": meta})
    return result

@data.post("/file-to-chunk")
async def file_to_chunk(db_id: str = Body(...), files: list[str] = Body(...), params: dict = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"File to chunk for db_id {db_id}: {files} {params=}")
    try:
        processed_files = await knowledge_base.save_files_for_pending_indexing(db_id, files, params)
        processed_failed_count = len([_p['status'] == 'failed' for _p in processed_files])
        processed_info = f"Processed {len(processed_files)} files for pending indexing, {processed_failed_count} files failed"
        return {"message": processed_info, "files": processed_files, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to process files for pending indexing: {e}, {traceback.format_exc()}")
        return {"message": f"Failed to process files for pending indexing: {e}", "status": "failed"}

@data.post("/url-to-chunk")
async def url_to_chunk(db_id: str = Body(...), urls: list[str] = Body(...), params: dict = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"Url to chunk for db_id {db_id}: {urls} {params=}")
    try:
        processed_urls = await knowledge_base.save_urls_for_pending_indexing(db_id, urls, params)
        return {"message": "URLs processed and pending indexing", "urls": processed_urls, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to process URLs for pending indexing: {e}, {traceback.format_exc()}")
        return {"message": f"Failed to process URLs for pending indexing: {e}", "status": "failed"}

@data.post("/add-by-file")
async def create_document_by_file(db_id: str = Body(...), files: list[str] = Body(...), current_user: User = Depends(get_admin_user)):
    raise ValueError("This method is deprecated. Use /file-to-chunk and /index-file instead.")

@data.post("/add-by-chunks")
async def add_by_chunks(db_id: str = Body(...), file_chunks: dict = Body(...), current_user: User = Depends(get_admin_user)):
    raise ValueError("This method is deprecated. Use /file-to-chunk and /index-file instead.")

@data.post("/index-file")
async def index_file(db_id: str = Body(...), file_id: str = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"Indexing file_id {file_id} in db_id {db_id}")
    try:
        result = await knowledge_base.trigger_file_indexing(db_id, file_id)
        return {"message": f"File {file_id} indexing initiated", "details": result, "status": "success"}
    except Exception as e:
        logger.error(f"Failed to index file {file_id}: {e}, {traceback.format_exc()}")
        return {"message": f"Failed to index file {file_id}: {e}", "status": "failed"}

@data.get("/info")
async def get_database_info(db_id: str, current_user: User = Depends(get_admin_user)):
    # logger.debug(f"Get database {db_id} info")
    database = knowledge_base.get_database_info(db_id)
    if database is None:
        raise HTTPException(status_code=404, detail="Database not found")
    return database

@data.delete("/document")
async def delete_document(db_id: str = Body(...), file_id: str = Body(...), current_user: User = Depends(get_admin_user)):
    logger.debug(f"DELETE document {file_id} info in {db_id}")
    knowledge_base.delete_file(db_id, file_id)
    return {"message": "删除成功"}

@data.get("/document")
async def get_document_info(db_id: str, file_id: str, current_user: User = Depends(get_admin_user)):
    logger.debug(f"GET document {file_id} info in {db_id}")

    try:
        info = knowledge_base.get_file_info(db_id, file_id)
    except Exception as e:
        logger.error(f"Failed to get file info, {e}, {db_id=}, {file_id=}, {traceback.format_exc()}")
        info = {"message": "Failed to get file info", "status": "failed"}

    return info

@data.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db_id: str | None = Query(None),
    current_user: User = Depends(get_admin_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    # 根据db_id获取上传路径，如果db_id为None则使用默认路径
    if db_id:
        upload_dir = knowledge_base.get_db_upload_path(db_id)
    else:
        upload_dir = os.path.join(config.save_dir, "data", "uploads")

    basename, ext = os.path.splitext(file.filename)
    filename = f"{basename}_{hashstr(basename, 4, with_salt=True)}{ext}".lower()
    file_path = os.path.join(upload_dir, filename)
    os.makedirs(upload_dir, exist_ok=True)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    return {"message": "File successfully uploaded", "file_path": file_path, "db_id": db_id}

@data.get("/graph")
async def get_graph_info(current_user: User = Depends(get_admin_user)):
    graph_info = graph_base.get_graph_info()
    if graph_info is None:
        raise HTTPException(status_code=400, detail="图数据库获取出错")
    return graph_info

@data.post("/graph/index-nodes")
async def index_nodes(data: dict = Body(default={}), current_user: User = Depends(get_admin_user)):
    if not graph_base.is_running():
        raise HTTPException(status_code=400, detail="图数据库未启动")

    # 获取参数或使用默认值
    kgdb_name = data.get('kgdb_name', 'neo4j')

    # 调用GraphDatabase的add_embedding_to_nodes方法
    count = graph_base.add_embedding_to_nodes(kgdb_name=kgdb_name)

    return {"status": "success", "message": f"已成功为{count}个节点添加嵌入向量", "indexed_count": count}

@data.get("/graph/node")
async def get_graph_node(entity_name: str, current_user: User = Depends(get_admin_user)):
    result = graph_base.query_node(entity_name=entity_name)
    return {"result": graph_base.format_query_result_to_graph(result), "message": "success"}

@data.get("/graph/nodes")
async def get_graph_nodes(kgdb_name: str, num: int, current_user: User = Depends(get_admin_user)):
    if not config.enable_knowledge_graph:
        raise HTTPException(status_code=400, detail="Knowledge graph is not enabled")

    logger.debug(f"Get graph nodes in {kgdb_name} with {num} nodes")
    result = graph_base.get_sample_nodes(kgdb_name, num)
    return {"result": graph_base.format_general_results(result), "message": "success"}

@data.post("/graph/add-by-jsonl")
async def add_graph_entity(file_path: str = Body(...), kgdb_name: str | None = Body(None), current_user: User = Depends(get_admin_user)):
    if not config.enable_knowledge_graph:
        return {"message": "知识图谱未启用", "status": "failed"}

    if not file_path.endswith('.jsonl'):
        return {"message": "文件格式错误，请上传jsonl文件", "status": "failed"}

    try:
        await graph_base.jsonl_file_add_entity(file_path, kgdb_name)
        return {"message": "实体添加成功", "status": "success"}
    except Exception as e:
        logger.error(f"添加实体失败: {e}, {traceback.format_exc()}")
        return {"message": f"添加实体失败: {e}", "status": "failed"}

@data.post("/update")
async def update_database_info(
    db_id: str = Body(...),
    name: str = Body(...),
    description: str = Body(...),
    current_user: User = Depends(get_admin_user)
):
    logger.debug(f"Update database {db_id} info: {name}, {description}")
    try:
        database = knowledge_base.update_database(db_id, name, description)
        return {"message": "更新成功", "database": database}
    except Exception as e:
        logger.error(f"更新数据库失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"更新数据库失败: {e}")

