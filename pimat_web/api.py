from flask_restful import Resource, reqparse, marshal, fields
from models import Schedules, Sensors, RelayLogger
from pimat_web.app import db

schedules_fields = {
    'start_time': fields.String,
    'stop_time': fields.String,
    'relay': fields.String,
    'id': fields.String
}


class SensorsAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=str, required=True, location='json')
        self.reqparse.add_argument('temperature1', type=float, default="", location='json')
        self.reqparse.add_argument('temperature2', type=float, default="", location='json')
        self.reqparse.add_argument('humidity', type=float, default="", location='json')
        self.reqparse.add_argument('light1', type=float, default="", location='json')
        self.reqparse.add_argument('pressure', type=float, default="", location='json')
        self.reqparse.add_argument('altitude', type=float, default="", location='json')
        self.reqparse.add_argument('source', type=str, required=True, location='json')
        super(SensorsAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        reading = Sensors(args['timestamp'], args['temperature1'], args['temperature2'], args['humidity'],
                          args['light1'], args['pressure'], args['altitude'], args['source'])
        db.session.add(reading)
        db.session.commit()
        return {'status': 'success'}, 201


class SchedulesAPI(Resource):
    def get(self):
        schedules = Schedules.query.order_by(Schedules.relay.asc()).all()
        return {'schedules': [marshal(schedule, schedules_fields) for schedule in schedules]}, 200


class RelayLoggerAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=str, required=True, location='json')
        self.reqparse.add_argument('relay', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('pin', type=int, required=True, default="", location='json')
        self.reqparse.add_argument('action', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('value', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('type', type=str, default="", location='json')
        self.reqparse.add_argument('source', type=str, required=True, default="", location='json')
        super(RelayLoggerAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        action = RelayLogger(args['timestamp'], args['relay'], args['pin'], args['action'], args['value'], args['type'],
                             args['source'])
        db.session.add(action)
        db.session.commit()

        return {'status': 'success'}, 201
