from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth import router
import conf
from ws import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_url = conf.get_db_url()
    engine = conf.get_engine(db_url)
    conf.init_db(engine)
    app.state.engine = engine
    yield


app = FastAPI(lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(router)
