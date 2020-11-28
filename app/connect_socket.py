import eventlet
import socketio
import json
from app.reader import Reader

sio = socketio.Server(cors_allowed_origins='*')
app = socketio.WSGIApp(sio)
hintCounter = 1

reader = Reader()


# return all elements containing key <key> set to value <value>
# based on https://stackoverflow.com/questions/9807634/
# find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
def gen_dict_extract(var, key, value):
    if isinstance(var, list):
        for d in var:
            for result in gen_dict_extract(d, key, value):
                yield result
    elif isinstance(var, dict):
        for k, v in var.items():
            if k == key and v == value:
                yield var
            if isinstance(v, dict) or isinstance(v, list):
                for result in gen_dict_extract(v, key, value):
                    yield result
    else:
        print('UNEXPECTED:', var)


@sio.on('connect')
def connect(sid, environ):
    print('connect ', sid)
    print('check all math:')
    sio.emit('check_all_math')


@sio.on('expressions')
def message_expressions(sid, data):
    print('expressions:\n', data)
    record = json.loads(data)
    reader.assignment_from_json_stream(record)
    print('Number of Assignments', len(reader.assignments))
    print('Number of Answers', len(reader.assignments[0].answers))


error_counter = 0


@sio.on('result')
def message_result(sid, data):
    global error_counter
    global hintCounter
    error_counter += 1
    print('result:\n', data)
    record = json.loads(data)
    hint = record['value']['hint'] if 'hint' in record['value'] else None
    if 'id' in record['value']:
        reader.add_error(record['docid'], record['problem'], record['value']['id'], record['value']['type'], hint)
        print("Error added to", record['docid'], record['problem'], record['value']['id'], record['value']['type'],
              hint)
    print(reader.assignments[0].to_json(2))

    assignment = reader.find_assign_with_id(record['docid'])
    answer = assignment.find_answer_with_mathid(record['mathid'])
    generated_highlight_id = answer.generate_highlight_intercept()
    print("trick error at" + generated_highlight_id)
    # add input boxes to real error
    sio.emit('add_input', json.dumps({
        "mathid": record["mathid"],
        "version": record["version"],
        "id": record["value"]["id"],
        "input-id": record["value"]["id"],
        "type": record["value"]["type"],
        "hint": "Type feedback here...",
        "mode": "set"
    }), room=sid)

    # add input box to generated error
    sio.emit('add_input', json.dumps({
        "mathid": record["mathid"],
        "version": record["version"],
        "id": generated_highlight_id,
        "input-id": generated_highlight_id,
        "color": "#ff5040",
        "type": record["value"]["type"],
        "hint": "Type feedback here...",
        "mode": "set"
    }), room=sid)

    # remove all hint
    sio.emit('set_hint', json.dumps({
        "mathid": record["mathid"],
        "version": record["version"],
        "id": record["value"]["id"],
        "type": record["value"]["type"],
        "mode": "set",
        "enable": False
    }), room=sid)


@sio.on('input_submit')
def print_result(sid, data):
    print('Student Response:\n', data)


@sio.on('disconnect')
def disconnect(sid):
    print('disconnect ', sid)


if __name__ == '__main__':
    eventlet.wsgi.server(eventlet.listen(('localhost', 3333)), app)
