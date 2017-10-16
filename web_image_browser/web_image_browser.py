#!/usr/bin/python3.6
import psycopg2
import os

from sanic import Sanic
from sanic import response
from jinja2 import Environment, FileSystemLoader, select_autoescape

app = Sanic()


def _orig_to_thumbnail(orig):
    bn = os.path.basename(orig)
    if len(bn.split('.')) == 1:
        return orig[:len(orig) - len(bn)] + 'thumbnails/' + bn + '.jpg'
    else:
        return orig[:len(orig) - len(bn)] + 'thumbnails/' + bn.split('.')[-2] + '.jpg'


@app.route("/")
async def hello(request):
    image_dicts = []

    cur.execute("SELECT name FROM newdraws ORDER BY ctime DESC;")
    for record in cur:
        image_dicts.append({
            'orig': record[0],
            'thumbnail': _orig_to_thumbnail(record[0])
        })
    conn.rollback()

    template = template_env.get_template('root.html')
    rendered_template = await template.render_async(images=image_dicts)
    return response.html(
        rendered_template,
        headers={
            'X-Served-By': 'sanic',
            'X-good': 'shit',
            'X-poop': ':poop:',
            'Response-time': '0',
            'Server-process-time': '0'},
        status=200
    )

if __name__ == "__main__":
    password = str(os.environ['NEWDRAWS_PG_PASSWORD'])
    conn_string = f'dbname=newdraws user=newdraws host=localhost password={password} port=5432'
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Load the template environment with async support
    template_env = Environment(
        loader=FileSystemLoader('./templates'),
        autoescape=select_autoescape(['html', 'xml']),
        enable_async=True
    )

    app.run(host="localhost", port=3000)
