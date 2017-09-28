#Web-CTRL-TL_ON-FAN_ON_1
#Web-STATUS
#Web-ALARM_SET-1506212153-TL_ON-FAN_ON_4
#Web-ALARM_RESET-1506212153
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import calendar
import time
from threading import Timer

webClients={}
alarm_thread_object={}

class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        print("Data Received: "+payload);
        data_parsed = payload.split("-")
        if data_parsed[1] == "LOGIN":
            webClients[data_parsed[0]] = self
            print("Device logged in: "+data_parsed[0])
        if data_parsed[1] == "ALARM_SET":
            self.alarm_manager_start(data_parsed[2],data_parsed[3],data_parsed[4],data_parsed[0])
        if data_parsed[1] == "ALARM_RESET":
            self.alarm_manager_stop(data_parsed[2],data_parsed[0])
        if data_parsed[1] == "CTRL":
            if data_parsed[0] in webClients:
                webClients[data_parsed[0]].sendMessage(data_parsed[1]+"-"+data_parsed[2]+"-"+data_parsed[3])
        if data_parsed[1] == "STATUS":
            if data_parsed[0] in webClients:
                webClients[data_parsed[0]].sendMessage(data_parsed[1])

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))

    def alarm_manager_start(self,alarm_time,light_state,fan_state,client):
        epoch_time = calendar.timegm(time.gmtime())
        if int(alarm_time)>epoch_time:
            diff_epoch = int(alarm_time) - epoch_time
            if client not in alarm_thread_object.iterkeys():
                alarm_thread_object[client]={}
            alarm_thread_object[client][alarm_time]=Timer(diff_epoch,self.alarm_trigger,[client,light_state,fan_state,alarm_time])
            alarm_thread_object[client][alarm_time].start()
            print("Alarm Enabled for client: "+client+" after: "+str(diff_epoch)+" seconds")
            webClients[client].sendMessage("Alarm Enabled for client: "+client+" after: "+str(diff_epoch)+" seconds")

    def alarm_manager_stop(self,alarm_time,client):
        if client in alarm_thread_object.iterkeys():
            if alarm_time in alarm_thread_object[client].iterkeys():
                alarm_thread_object[client][alarm_time].cancel()
                del alarm_thread_object[client][alarm_time]
                print("Alarm Disabled for client: "+client+" at time: "+str(alarm_time)+" seconds")
                webClients[client].sendMessage("Alarm Disabled for client: "+client+" at time: "+str(alarm_time)+" seconds")


    def alarm_trigger(self,client,light_state,fan_state,alarm_time):
        webClients[client].sendMessage("CTRL-"+light_state+"-"+fan_state)
        print("Alarm triggered for client: "+client+" at time: "+str(alarm_time)+" seconds")


if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor

    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory(u"ws://35.163.167.156:9090")
    factory.protocol = MyServerProtocol
    reactor.listenTCP(9090, factory)
    reactor.run()