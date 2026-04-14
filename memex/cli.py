"""
CLI — Memex 命令行工具
"""
import json
import sys
from typing import Optional

import click

from ._types import MemoryRecord, MemoryType, DEFAULT_IMPORTANCE
from ._config import load_config, save_config, get_storage_path
from .store.factory import create_store
from . import _embed as embed_module


@click.group()
def cli():
    """Memex — Agent 记忆系统"""
    pass


@cli.command()
def init():
    """初始化 Memex（使用默认配置配置）"""
    config = load_config()
    
    # 确保存储目录存在
    storage_path = get_storage_path()
    
    click.echo(f"   存储路径: {storage_path}")
    click.echo(f"   向量数据库: {config.vector_store.provider}")
    click.echo(f"   Embedding 模型: {config.embedding.model}")
    click.echo(f"下载Embedding模型...")
    
    # 预热 embedding 模型（下载 + 验证）
    embed_module.get_model()
    
    click.echo(f"✅ 初始化完成")


@cli.command()
def install_skill():
    """安装 Skill 到 ~/.agents/skills/memex/（供 Agent 系统使用）"""
    import os
    import shutil
    
    skill_src = os.path.join(os.path.dirname(__file__), "SKILL.md")
    skill_dest_dir = os.path.expanduser("~/.agents/skills/memex")
    skill_dest = os.path.join(skill_dest_dir, "SKILL.md")
    
    if not os.path.exists(skill_src):
        click.echo(f"❌ SKILL.md 未找到: {skill_src}")
        return
    
    os.makedirs(skill_dest_dir, exist_ok=True)
    shutil.copy2(skill_src, skill_dest)
    click.echo(f"✅ Skill 已安装到: {skill_dest}")


@cli.command()
@click.option("--type", "-t", "memory_type", required=True, 
              type=click.Choice([t.value for t in MemoryType]))
@click.option("--content", "-c", required=True, help="记忆内容")
@click.option("--repo", "-r", default="default", help="命名空间")
@click.option("--importance", "-i", type=float, help="重要性 0-1")
@click.option("--confidence", type=float, default=0.8, help="确定性 0-1")
@click.option("--title", help="标题")
def save(memory_type: str, content: str, repo: str, importance: Optional[float], 
         confidence: float, title: str):
    """保存记忆"""
    # 获取类型
    mtype = MemoryType(memory_type)
    
    # 确定 importance
    if importance is None:
        importance = DEFAULT_IMPORTANCE[mtype]
    
    # 创建记录
    record = MemoryRecord(
        type=mtype,
        content=content,
        raw_text=content,
        importance=importance,
        confidence=confidence,
        repo=repo,
        title=title or "",
    )
    
    # 生成 embedding
    vector = embed_module.embed_text(content)
    
    # 存储
    store = create_store()
    store.add(record, vector)
    store.close()
    
    click.echo(f"✅ 记忆已保存: {record.id[:8]}...")
    click.echo(f"   类型: {memory_type}")
    click.echo(f"   内容: {content[:50]}...")


@cli.command()
@click.argument("query")
@click.option("--repo", "-r", help="命名空间")
@click.option("--limit", "-l", default=10, help="返回数量")
def search(query: str, repo: Optional[str], limit: int):
    """语义搜索记忆"""
    # 生成 query 向量
    query_vector = embed_module.embed_text(query)
    
    # 搜索
    store = create_store()
    results = store.search(query_vector, repo=repo, limit=limit)
    store.close()
    
    if not results:
        click.echo("未找到相关记忆")
        return
    
    # 输出 JSON（供 Agent 解析）
    output = {
        "query": query,
        "results": [
            {
                "id": r.id,
                "type": r.type.value,
                "content": r.content,
                "importance": r.importance,
                "confidence": r.confidence,
                "stability": r.stability,
                "score": score,
            }
            for r, score in results
        ],
        "total": len(results),
    }
    
    click.echo(json.dumps(output, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("memory_id")
def get(memory_id: str):
    """获取单条记忆"""
    store = create_store()
    record = store.get(memory_id)
    store.close()
    
    if not record:
        click.echo(f"未找到记忆: {memory_id}")
        sys.exit(1)
    
    click.echo(json.dumps(record.to_dict(), ensure_ascii=False, indent=2))


@cli.command()
@click.option("--repo", "-r", help="命名空间")
@click.option("--type", "-t", help="记忆类型")
@click.option("--limit", "-l", default=20, help="返回数量")
def list(repo: Optional[str], type: Optional[str], limit: int):
    """列出记忆"""
    store = create_store()
    records = store.list(repo=repo, type=type, limit=limit)
    store.close()
    
    if not records:
        click.echo("没有记忆")
        return
    
    for r in records:
        click.echo(f"[{r.type.value}] {r.content[:60]}... ({r.id[:8]})")


@cli.command()
@click.argument("memory_id")
def delete(memory_id: str):
    """删除记忆"""
    store = create_store()
    store.delete(memory_id)
    store.close()
    
    click.echo(f"✅ 已删除: {memory_id[:8]}...")


@cli.command()
@click.option("--repo", "-r", help="命名空间")
def stats(repo: Optional[str]):
    """查看统计"""
    store = create_store()
    count = store.count(repo=repo)
    store.close()
    
    click.echo(f"记忆总数: {count}")
    if repo:
        click.echo(f"命名空间: {repo}")


@cli.command()
def config_show():
    """显示当前配置"""
    config = load_config()
    click.echo(config.model_dump_json(indent=2))


# 隐私控制命令
@cli.command()
@click.option("--repo", "-r", help="命名空间")
def recall(repo: Optional[str]):
    """查看被记住的内容（隐私控制）"""
    store = create_store()
    records = store.list(repo=repo, limit=1000)
    store.close()
    
    if not records:
        click.echo("没有被记住的内容")
        return
    
    click.echo(f"你被记住了 {len(records)} 条记忆：\n")
    for r in records:
        click.echo(f"  [{r.type.value}] {r.content[:80]}")


@cli.command()
@click.argument("memory_id", required=False)
@click.option("--all", "purge_all", is_flag=True, help="清空所有记忆")
def purge(memory_id: Optional[str], purge_all: bool):
    """删除记忆（隐私控制）"""
    if not memory_id and not purge_all:
        click.echo("请指定 memory_id 或使用 --all")
        sys.exit(1)
    
    if purge_all:
        if not click.confirm("确定要清空所有记忆吗？"):
            return
        
        store = create_store()
        records = store.list(limit=10000)
        for r in records:
            store.delete(r.id)
        store.close()
        
        click.echo("✅ 已清空所有记忆")
    else:
        store = create_store()
        store.delete(memory_id)
        store.close()
        
        click.echo(f"✅ 已删除: {memory_id[:8]}...")


if __name__ == "__main__":
    cli()
