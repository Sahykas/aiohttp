import json
from aiohttp import web
from models import engine, Session, Ads, Base

from sqlalchemy.exc import IntegrityError

app = web.Application()


async def context_orm(app: web.Application):
    print("START")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print("STOP")


@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request["session"] = session
        response = await handler(request)
        return response


app.cleanup_ctx.append(context_orm)
app.middlewares.append(session_middleware)


def get_http_error(error_class, description: str):
    return error_class(
        text=json.dumps({"status": "error", "description": description}),
        content_type="application/json",
    )


async def get_ads(ads_id, session: Session):
    ads = await session.get(Ads, ads_id)
    if ads is None:
        raise get_http_error(web.HTTPNotFound, "Ads not found")
    return ads


async def add_ads(ads: Ads, session: Session):
    try:
        session.add(ads)
        await session.commit()
    except IntegrityError as er:
        raise get_http_error(web.HTTPConflict, 'Ads already exists')
    return ads


class AdsView(web.View):
    @property
    def session(self):
        return self.request["session"]

    @property
    def ads_id(self):
        return int(self.request.match_info["ads_id"])

    async def get(self):
        ads = await get_ads(self.ads_id, self.session)
        return web.json_response({'id': ads.id,
                                  'title': ads.title,
                                  'creation_time': ads.creation_time.isoformat()})

    async def post(self):
        json_validated = await self.request.json()
        ads = Ads(**json_validated)
        await add_ads(ads, self.session)
        return web.json_response({'id': ads.id})


    async def delete(self):
        ads = await get_ads(self.ads_id, self.session)
        await self.session.delete(ads)
        await self.session.commit()
        return web.json_response({
            'status': 'success'
        })


app.add_routes(
    [
        web.post("/ads", AdsView),
        web.get("/ads/{ads_id:\d+}", AdsView),
        web.patch("/ads/{ads_id:\d+}", AdsView),
        web.delete("/ads/{ads_id:\d+}", AdsView),
    ]
)
if __name__ == "__main__":
    web.run_app(app)
