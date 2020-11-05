# a builder
import json
from app.assignment import Assignment
from app.answer import Answer


class Reader:
    def from_json_file(self, fn):
        with open(fn) as f:
            data = json.load(f)
        print('API response data: ', data)
        return self.from_json_stream(data)

    def from_json_stream(self, data):
        docid = data['docid']
        docname = data['docname']
        userid = data['userid']
        username = data['username']
        assignment = Assignment(docid, docname, userid, username)
        mathid = data['mathid']
        version = data['version']
        problem = data['problem']
        expression = data['value']
        answer = Answer.from_json(mathid, version, problem, expression)
        assignment.add_answer(answer)
        return assignment
