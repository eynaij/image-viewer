import os
import sys
import cv2
import glob
import json
import yaml
import logging
import argparse
from io import BytesIO
from flask import Flask, request, jsonify, send_file, abort, render_template, g, redirect, url_for, Response, session
from image_viewer.db import Db

# from draw_hds_anno import draw_annotation

# reload(sys)
import importlib
importlib.reload(sys)
# sys.setdefaultencoding("utf-8")

logging.basicConfig(
        level       = logging.DEBUG,
        format      = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#        filename    = 'run.log',
#        filemode    = 'a')

app = Flask(__name__, instance_relative_config=True)

_CFGROOT = os.path.join(os.environ['HOME'], '.image-viewer')
cfgfile = os.path.join(_CFGROOT, 'image-viewer.yaml')
with open(cfgfile, 'r') as fid:
    cfg = yaml.load(fid.read(), Loader=yaml.SafeLoader)

#app.config.update(json.load(open('config/config.json')))
app.config.update(cfg)

def api_response(status, message, data={}, code=None):
    result = {'status'  : status,
              'message' : message,
              'data'    : data}
    if code is None:
        return jsonify(result)
    else:
        return jsonify(result), code

def get_db():
    if not hasattr(g, 'db'):
        database_file = os.path.join(_CFGROOT, app.config['database'])
        g.db = Db(database_file, app.logger)
    return g.db

def get_image_list(directory, name_formats):
    image_paths = list()
    for name_format in name_formats:
        image_paths.extend(glob.glob(os.path.join(directory, name_format)))
    image_paths = filter(lambda path: check_path_permission(path), image_paths)
    image_keys = map(lambda image_path: image_path[len(directory)+1:], image_paths)
    return sorted(image_keys)

def get_hds_json_data_list(directory, name_formats):
    image_dict = dict()
    for name_format in name_formats:
        json_paths = glob.glob(os.path.join(directory, name_format))
        json_paths = filter(lambda path: check_path_permission(path), json_paths)
        for json_path in json_paths:
            image_prefix = os.path.relpath(os.path.splitext(json_path)[0], directory)
            with open(json_path) as fin:
                for line in fin:
                    record = json.loads(line)
                    image_key = os.path.join(image_prefix, record['image_key'])
                    record['image_key'] = image_key
                    if image_key not in image_dict:
                        image_dict[image_key] = json.dumps(record)
    image_keys = sorted(image_dict)
    annotations = map(lambda image_key: image_dict[image_key], image_keys)
    return image_keys, annotations

def check_path_permission(path):
    return any(list(map(lambda dir_ : os.path.abspath(path).startswith(os.path.abspath(dir_)), app.config['permitted_dirs'])))

@app.route('/', methods=['GET'])
def view_index():
    return redirect(url_for('handle_browser'))

@app.route('/annotator', methods=['GET'])
def handle_annotator():
    return render_template('annotator.html')

@app.route('/browser', methods=['GET'])
def handle_browser():
    if 'dir' not in request.args:
        if 'default_dir' in app.config:
            filepath = app.config['default_dir']
        else:
            filepath = app.config['permitted_dirs'][0]
        return redirect('%s?dir=%s' % (url_for('handle_browser'), filepath))
    else:
        filepath = request.args['dir']
    filepath = os.path.abspath(filepath)
    if not os.path.exists(filepath):
        abort(404, 'File does not exist.')
    elif not check_path_permission(filepath):
        abort(404, 'Permission denied.')
    else:
        try:
            filenames = sorted(os.listdir(filepath))
        except OSError:
            abort(404, 'Permission denied.')

        files = [{'name'    : filename,
                  'url'     : '/filesystem' + os.path.join(filepath, filename)}
                        for filename in filenames]
        files = [{'name'    : '. .',
                  'url'     : '/filesystem' + os.path.dirname(filepath)}] + files
        return render_template('browser.html', filepath=filepath, files=files)

@app.route('/tasks', methods=['GET'])
def view_tasks():
    return render_template('tasks.html')

@app.route('/filesystem/', methods=['GET'])
def handle_filesystem_root():
    return handle_filesystem('')

@app.route('/render-image/<int:image_id>', methods=['GET'])
def handle_render(image_id):
    config = json.loads(request.args.get('config', '{}'))
    db = get_db()
    images = db.select_images_with_id(image_id)
    if not len(images):
        abort(404)
    image = images[0]
    annotation = json.loads(image['annotation'])
    tasks = db.select_tasks_with_id(image['task_id'])
    task = tasks[0]
    filepath = os.path.join(task['directory_key'], image['image_key'])
    image = cv2.imread(filepath.encode('utf-8'))
    # draw_annotation(image, annotation, **config)
    image_bin = cv2.imencode('.jpg', image)[1]
    image_file = BytesIO(image_bin)
    return Response(image_file, mimetype="image/jpeg")


@app.route('/filesystem/<path:filepath>', methods=['GET'])
def handle_filesystem(filepath):
    filepath = os.path.join('/', filepath)
    filepath = os.path.abspath(filepath)
    height = request.args.get('height', None)
    if not check_path_permission(filepath):
        abort(404, 'Permission denied.')
    elif not os.path.exists(filepath):
        abort(404, 'File does not exist.')
    elif os.path.isdir(filepath):
        return redirect('%s?dir=%s' % (url_for('handle_browser'), filepath))
    else:
        if height:
            height = int(height)
            image = cv2.imread(filepath.encode('utf-8'))
            h, w, c = image.shape
            scale = float(height) / h
            width = int(w * scale)
            image = cv2.resize(image, (width, height))
            image_bin = cv2.imencode('.jpg', image)[1]
            image_file = BytesIO(image_bin)
            return Response(image_file, mimetype="image/jpeg")
#            return image_file
        else:
            return send_file(filepath)

@app.route('/api/tasks', methods=['POST'])
def create_task():
    directory = os.path.abspath(request.form['dir'])
    name_formats = request.form['formats']
    offset = int(request.form['offset'])
    stride = int(request.form['stride'])
    task_type = request.form['type']

    name_formats = name_formats.split(';')

    if task_type == 'image':
        image_keys = get_image_list(directory, name_formats)
        image_keys = image_keys[offset::stride]
        annotations = None
    elif task_type == 'hds_json':
        image_keys, annotations = get_hds_json_data_list(directory, name_formats)
        annotations = annotations[offset::stride]

    db = get_db()

    task_id = db.insert_task(
            directory_key   = directory,
            task_type       = task_type
            )
    if task_id:
        db.insert_images(
                task_id     = task_id,
                image_keys  = image_keys,
                annotations = annotations
                )
        status = 1
        message = 'Create task success.'
        data = {'task_id'   : task_id}
    else:
        status = 0
        message = 'Create task failure.'
        data = {}
    return api_response(status, message, data)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    db = get_db()
    tasks = db.select_tasks()
    status = 1
    message = 'Query tasks success.'
    data = {'tasks' : tasks}
    return api_response(status, message, data)

@app.route('/api/tasks/<int:task_id>/images', methods=['GET'])
def get_task_images(task_id):
    pagesize = int(request.args['pagesize'])
    page = int(request.args['page'])
    db = get_db()
    tasks = db.select_tasks_with_id(task_id)
    if not len(tasks):
        status = 0
        message = 'Task dose not exist.'
        data = {}
        code = 404
    else:
        task = tasks[0]
        directory = task['directory_key']
        task_type = task['type']
        status = 1
        message = 'Query images success.'
        offset = (page-1)*pagesize
        images = db.select_images_with_task(task_id, limit=pagesize, offset=offset)
        for idx, image in enumerate(images):
            if task_type == 'image':
                image['url'] = '/filesystem' + os.path.join(directory, image['image_key'])
            elif task_type == 'hds_json':
                image['url'] = url_for('handle_render', image_id=image['image_id'])
            image['idx'] = idx + offset + 1
        data = {'images' : images}
        code = 200
    return api_response(status, message, data, code)


@app.route('/api/submitter', methods=['POST'])
def handle_submitter():
    image_id = request.form['image_id']
    selected = request.form['selected']

    db = get_db()
    if not db.update_image_selection(
            image_id        = image_id,
            selected        = selected):
        status = 0
        if not len(db.select_images_with_id(image_id)):
            message = 'Image does not exist.'
            code = 404
        else:
            message = 'Selected value error.'
            code = 400
    else:
        status = 1
        message = 'Update selection failure.'
        code = 200
    return api_response(status, message, code=code)

@app.route('/results/task_<int:task_id>.json', methods=['GET'])
def get_result(task_id):
    db = get_db()
    tasks = db.select_tasks_with_id(task_id)
    if not len(tasks):
        abort(404)
    else:
        images = db.select_selected_images_with_task(task_id)
        data = {'directory' : tasks[0]['directory_key'],
                'images'    : [image['image_key'] for image in images]}
        return jsonify(data)

@app.route('/api/auth', methods=['POST'])
def handle_login():
    password = request.form['password']
    if password == app.config['password']:
        session['auth'] = True
        message = 'Login success'
        status = 1
    else:
        message = 'Invalid password'
        status = 0
    data = {}
    return api_response(status, message, data)

@app.route('/api/auth', methods=['GET'])
def handle_get_auth_info():
    if session.get('auth', None):
        status = 1
        message = 'logined'
    else:
        status = 0
        message = 'Not login'
    data = {}
    return api_response(status, message, data)

@app.route('/api/auth', methods=['DELETE'])
def handle_logout():
    if session.pop('auth', None):
        status = 1
        message = 'Logout'
    else:
        status = 0
        message = 'Not login'
    data = {}
    return api_response(status, message, data)

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def handle_delete_task(task_id):
    if session.get('auth', None):
        db = get_db()
        result = db.delete_tasks_with_id(task_id)
        if result:
            message = 'Deleted task %d' % task_id
            status = 1
        else:
            message = 'Delete task %d failed' % task_id
            status = 0
    else:
        status = 0
        message = 'login required'
    data = {}
    return api_response(status, message, data)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', type=str)
    parser.add_argument('--port', default=8000, type=int)
    parser.add_argument('--cfg', default='config/config.json', type=str)
    parser.add_argument('--threaded', default=1, type=int)
    parser.add_argument('--debug', default=0, type=int)
    return parser.parse_args()

if __name__ == '__main__':
    # not used
    args = parse_args()
    app.config.update(json.load(open(args.cfg)))

    app.run(
            host        = args.host,
            port        = args.port,
            threaded    = args.threaded,
            debug       = args.debug)
