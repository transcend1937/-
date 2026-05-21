"""知识库搜索工具 - 用于查询铁路局招录数据等就业信息"""

from langchain.tools import tool
from coze_coding_dev_sdk import KnowledgeClient, Config
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


@tool
def search_knowledge(query: str) -> str:
    """在就业知识库中搜索相关信息，包括铁路局招录数据、岗位信息、行业趋势等。当用户询问具体的就业数据、路局招录情况、专业录取人数等信息时，使用此工具获取真实数据。

    Args:
        query: 搜索关键词，例如"广州局招录数据""铁道机车专业录取人数""南昌局女生比例"等
    """
    ctx = request_context.get() or new_context(method="search_knowledge")

    try:
        config = Config()
        client = KnowledgeClient(config=config, ctx=ctx)

        response = client.search(
            query=query,
            top_k=5,
            min_score=0.5
        )

        if response.code != 0:
            return f"知识库搜索失败: {response.msg}"

        if not response.chunks:
            return "未在知识库中找到相关信息。"

        results = []
        for i, chunk in enumerate(response.chunks, 1):
            results.append(
                f"【结果{i}】(相关度:{chunk.score:.2f})\n{chunk.content}"
            )

        return "\n\n".join(results)

    except Exception as e:
        return f"知识库搜索时发生错误: {str(e)}"