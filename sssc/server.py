import asyncio
from tornado.web import Application
from api.v1.run import RunHandler

def make_app():
    return Application([
        (r"/run", RunHandler),
    ])

async def main():
    app = make_app()
    app.listen(29681)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())