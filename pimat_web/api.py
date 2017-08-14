from flask_restful import Resource, reqparse, marshal, fields
from models import db, Sensors, Schedules, RelayLogger, Monitoring

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


class MonitoringAPI(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=str, required=True, location='json')
        self.reqparse.add_argument('hostname', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('ip_eth0', type=str, default="", location='json')
        self.reqparse.add_argument('ip_wlan0', type=str, default="", location='json')
        self.reqparse.add_argument('timezone', type=str, default="", location='json')
        self.reqparse.add_argument('boot_time', type=float, default="", location='json')
        self.reqparse.add_argument('cpu_temp', type=float, default="", location='json')
        self.reqparse.add_argument('cpu_usage', type=float, default="", location='json')
        self.reqparse.add_argument('cpu_frequency', type=float, default="", location='json')
        self.reqparse.add_argument('load_1', type=float, default="", location='json')
        self.reqparse.add_argument('load_5', type=float, default="", location='json')
        self.reqparse.add_argument('load_15', type=float, default="", location='json')
        self.reqparse.add_argument('total_proc', type=int, default="", location='json')
        self.reqparse.add_argument('ram_total', type=str, default="", location='json')
        self.reqparse.add_argument('ram_free', type=str, default="", location='json')
        self.reqparse.add_argument('ram_used', type=str, default="", location='json')
        self.reqparse.add_argument('ram_used_percent', type=float, default="", location='json')
        self.reqparse.add_argument('swap_total', type=str, default="", location='json')
        self.reqparse.add_argument('swap_free', type=str, default="", location='json')
        self.reqparse.add_argument('swap_used', type=str, default="", location='json')
        self.reqparse.add_argument('swap_used_percent', type=float, default="", location='json')
        self.reqparse.add_argument('disk_total', type=str, default="", location='json')
        self.reqparse.add_argument('disk_used', type=str, default="", location='json')
        self.reqparse.add_argument('disk_free', type=str, default="", location='json')
        self.reqparse.add_argument('disk_used_percent', type=float, default="", location='json')
        self.reqparse.add_argument('disk_total_boot', type=str, default="", location='json')
        self.reqparse.add_argument('disk_used_boot', type=str, default="", location='json')
        self.reqparse.add_argument('disk_free_boot', type=str, default="", location='json')
        self.reqparse.add_argument('disk_used_percent_boot', type=float, default="", location='json')
        self.reqparse.add_argument('eth0_received', type=str, default="", location='json')
        self.reqparse.add_argument('eth0_sent', type=str, default="", location='json')
        self.reqparse.add_argument('wlan0_received', type=str, default="", location='json')
        self.reqparse.add_argument('wlan0_sent', type=str, default="", location='json')
        self.reqparse.add_argument('lo_received', type=str, default="", location='json')
        self.reqparse.add_argument('lo_sent', type=str, default="", location='json')
        self.reqparse.add_argument('kernel', type=str, default="", location='json')
        self.reqparse.add_argument('source', type=str, default="", required=True, location='json')
        super(MonitoringAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        action = Monitoring(args['timestamp'], args['hostname'], args['ip_eth0'], args['ip_wlan0'], args['timezone'],
                            args['boot_time'], args['cpu_temp'], args['cpu_usage'], args['cpu_frequency'],
                            args['load_1'], args['load_5'], args['load_15'], args['total_proc'], args['ram_total'],
                            args['ram_free'], args['ram_used'], args['ram_used_percent'], args['swap_total'],
                            args['swap_free'], args['swap_used'], args['swap_used_percent'], args['disk_total'],
                            args['disk_used'], args['disk_free'], args['disk_used_percent'],args['disk_total_boot'],
                            args['disk_used_boot'], args['disk_free_boot'], args['disk_used_percent_boot'],
                            args['eth0_received'], args['eth0_sent'], args['wlan0_received'], args['wlan0_sent'],
                            args['lo_received'], args['lo_sent'], args['kernel'], args['source'])
        db.session.add(action)
        db.session.commit()

        return {'status': 'success', 'data': args}, 201
