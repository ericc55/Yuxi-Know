import os
from datetime import datetime
from zoneinfo import ZoneInfo

from loguru import logger as loguru_logger

DATETIME = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d-%H%M%S')
# DATETIME = "debug" # 为了方便，调试的时候输出到 debug.log 文件
LOG_FILE = f'saves/log/project-{DATETIME}.log'
def setup_logger(name, level="DEBUG", console=True):
    """使用 loguru 设置日志记录器"""
    os.makedirs("saves/log", exist_ok=True)

    # 移除默认的 handler
    loguru_logger.remove()

    # 添加文件日志（无颜色）
    loguru_logger.add(
        LOG_FILE,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {name} - {message}",
        encoding="utf-8",
        rotation="10 MB",  # 文件大小达到 10MB 时轮转
        retention="30 days",  # 保留30天的日志
        compression="zip"  # 压缩旧日志文件
    )

    # 添加控制台日志（有颜色）
    if console:
        loguru_logger.add(
            lambda msg: print(msg, end=""),
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> - <level>{level}</level> - <cyan>{name}</cyan> - <level>{message}</level>",
            colorize=True
        )

    return loguru_logger


# 设置根日志记录器
logger = setup_logger('Yuxi')

__all__ = ['logger']

# If you want to disable logging from external libraries
# logging.getLogger('some_external_library').setLevel(logging.CRITICAL)
