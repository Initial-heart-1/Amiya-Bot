import re

from core.database.messages import *
from core.database.group import GroupSetting
from core.util import TimeRecorder
from core import bot, websocket, http, custom_chain, Message, Chain

from .helper import WeiboUser, WeiboContent, weibo_conf, set_push_group


@table
class WeiboRecord(MessageBaseModel):
    user_id: int = IntegerField()
    blog_id: str = TextField()
    record_time: int = IntegerField()


async def send_by_index(index: int, weibo: WeiboUser, data: Message):
    result = await weibo.get_weibo_content(index - 1)

    if not result:
        return Chain(data).text('博士…暂时无法获取微博呢…请稍后再试吧')
    else:
        return Chain(data).text(result.html_text).text('\n').text(result.detail_url).image(result.pics_list)


@bot.on_group_message(function_id='weibo', keywords=['公告', '动态', '消息', '微博'])
async def _(data: Message):
    message = data.text_digits
    index = 0

    r = re.search(r'(\d+)', message)
    if r:
        index = abs(int(r.group(1)))

    if '最新' in message:
        index = 1

    weibo = WeiboUser(weibo_conf.listen[0])

    if index:
        return await send_by_index(index, weibo, data)
    else:
        result = await weibo.get_blog_list()
        if not result:
            return Chain(data).text('博士…暂时无法获取微博列表呢…请稍后再试吧')

        wait = await data.waiting(
            Chain(data).text_image(result).text('回复【序号】或和我说「阿米娅第 N 条微博」来获取详情吧')
        )
        if wait:
            r = re.search(r'(\d+)', wait.text_digits)
            if r:
                index = abs(int(r.group(1)))
                return await send_by_index(index, weibo, wait)


@bot.timed_task(each=30)
async def _():
    for user in weibo_conf.listen:
        weibo = WeiboUser(user)
        new_id = await weibo.get_weibo_id(0)
        if not new_id:
            continue

        record = WeiboRecord.get_or_none(blog_id=new_id)
        if record:
            continue

        await set_push_group()

        group_list = [item['group_id'] for item in await http.get_group_list()]
        enables_list = [int(item.group_id) for item in GroupSetting.select().where(GroupSetting.send_weibo == 1)]
        target = list(
            set(group_list).intersection(
                set(enables_list)
            )
        )

        WeiboRecord.create(
            user_id=user,
            blog_id=new_id,
            record_time=int(time.time())
        )

        async with websocket.send_to_admin() as chain:
            chain.text(f'开始推送微博:\n{new_id}\n目标群数: {len(target)}')

        time_rec = TimeRecorder()
        result = await weibo.get_weibo_content(0)

        for group_id in target:
            data = custom_chain(group_id=group_id)

            data.text(result.html_text)
            data.text('\n')
            data.text(result.detail_url)
            data.image(result.pics_list)

            await websocket.send(data)
            await asyncio.sleep(0.5)

        async with websocket.send_to_admin() as chain:
            chain.text(f'微博推送结束:\n{new_id}\n耗时{time_rec.total()}')
