from flask import request
from flask_security import current_user
from flask_socketio import join_room, leave_room, emit

from classes.shared import db, socketio
from classes import settings
from classes import Channel
from classes import Stream

from functions import webhookFunc
from functions import templateFilters

from functions.socketio.stream import handle_viewer_total_request

from app import r

@socketio.on('disconnect')
def disconnect():

    return 'OK'

@socketio.on('newViewer')
def handle_new_viewer(streamData):
    channelLoc = str(streamData['data'])

    sysSettings = settings.settings.query.first()

    requestedChannel = Channel.Channel.query.filter_by(channelLoc=channelLoc).first()
    stream = Stream.Stream.query.filter_by(streamKey=requestedChannel.streamKey).first()

    userSID = request.cookies.get('ospSession')

    streamSIDList = r.smembers(channelLoc + '-streamSIDList')
    if streamSIDList is None:
        r.sadd(channelLoc + '-streamSIDList', userSID)
    elif userSID.encode('utf-8') not in streamSIDList:
        r.sadd(channelLoc + '-streamSIDList', userSID)

    currentViewers = len(streamSIDList)

    streamName = ""
    streamTopic = 0

    requestedChannel.currentViewers = currentViewers
    db.session.commit()

    if stream is not None:
        stream.currentViewers = currentViewers
        db.session.commit()
        streamName = stream.streamName
        streamTopic = stream.topic

    else:
        streamName = requestedChannel.channelName
        streamTopic = requestedChannel.topic

    if requestedChannel.imageLocation is None:
        channelImage = (sysSettings.siteProtocol + sysSettings.siteAddress + "/static/img/video-placeholder.jpg")
    else:
        channelImage = (sysSettings.siteProtocol + sysSettings.siteAddress + "/images/" + requestedChannel.imageLocation)

    join_room(streamData['data'])

    if requestedChannel.showChatJoinLeaveNotification:
        if current_user.is_authenticated:
            pictureLocation = current_user.pictureLocation
            if current_user.pictureLocation is None:
                pictureLocation = '/static/img/user2.png'
            else:
                pictureLocation = '/images/' + pictureLocation

            streamUserList = r.smembers(channelLoc + '-streamUserList')
            if streamUserList is None:
                r.rpush(channelLoc + '-streamUserList', current_user.username)
            elif current_user.username.encode('utf-8') not in streamUserList:
                r.rpush(channelLoc + '-streamUserList', current_user.username)

            emit('message', {'user':'Server','msg': current_user.username + ' has entered the room.', 'image': pictureLocation}, room=streamData['data'])
        else:
            emit('message', {'user':'Server','msg': 'Guest has entered the room.', 'image': '/static/img/user2.png'}, room=streamData['data'])

    else:
        if current_user.is_authenticated:
            r.rpush(channelLoc + '-streamUserList', current_user.username)

    if current_user.is_authenticated:
        pictureLocation = current_user.pictureLocation
        if current_user.pictureLocation is None:
            pictureLocation = '/static/img/user2.png'
        else:
            pictureLocation = '/images/' + pictureLocation

        webhookFunc.runWebhook(requestedChannel.id, 2, channelname=requestedChannel.channelName,
                   channelurl=(sysSettings.siteProtocol + sysSettings.siteAddress + "/channel/" + str(requestedChannel.id)),
                   channeltopic=requestedChannel.topic, channelimage=channelImage, streamer=templateFilters.get_userName(requestedChannel.owningUser),
                   channeldescription=str(requestedChannel.description), streamname=streamName, streamurl=(sysSettings.siteProtocol + sysSettings.siteAddress + "/view/" + requestedChannel.channelLoc),
                   streamtopic=templateFilters.get_topicName(streamTopic), streamimage=(sysSettings.siteProtocol + sysSettings.siteAddress + "/stream-thumb/" + requestedChannel.channelLoc + ".png"),
                   user=current_user.username, userpicture=(sysSettings.siteProtocol + sysSettings.siteAddress + str(pictureLocation)))
    else:
        webhookFunc.runWebhook(requestedChannel.id, 2, channelname=requestedChannel.channelName,
                   channelurl=(sysSettings.siteProtocol + sysSettings.siteAddress + "/channel/" + str(requestedChannel.id)),
                   channeltopic=requestedChannel.topic, channelimage=channelImage, streamer=templateFilters.get_userName(requestedChannel.owningUser),
                   channeldescription=str(requestedChannel.description), streamname=streamName,
                   streamurl=(sysSettings.siteProtocol + sysSettings.siteAddress + "/view/" + requestedChannel.channelLoc),
                   streamtopic=templateFilters.get_topicName(streamTopic), streamimage=(sysSettings.siteProtocol + sysSettings.siteAddress + "/stream-thumb/" + requestedChannel.channelLoc + ".png"),
                   user="Guest", userpicture=(sysSettings.siteProtocol + sysSettings.siteAddress + '/static/img/user2.png'))

    handle_viewer_total_request(streamData, room=streamData['data'])

    db.session.commit()
    db.session.close()
    return 'OK'

@socketio.on('removeViewer')
def handle_leaving_viewer(streamData):
    channelLoc = str(streamData['data'])

    requestedChannel = Channel.Channel.query.filter_by(channelLoc=channelLoc).first()
    stream = Stream.Stream.query.filter_by(streamKey=requestedChannel.streamKey).first()

    userSID = request.cookies.get('ospSession')

    streamSIDList = r.smembers(channelLoc + '-streamSIDList')
    if streamSIDList is not None:
        r.srem(channelLoc + '-streamSIDList', userSID)

    currentViewers = len(streamSIDList)

    requestedChannel.currentViewers = currentViewers
    if requestedChannel.currentViewers < 0:
        requestedChannel.currentViewers = 0
    db.session.commit()

    if stream is not None:
        stream.currentViewers = currentViewers
        if stream.currentViewers < 0:
            stream.currentViewers = 0
        db.session.commit()
    leave_room(streamData['data'])

    if current_user.is_authenticated:
        streamUserList = r.lrange(channelLoc + '-streamUserList', 0, -1)
        if streamUserList is not None:
            r.lrem(channelLoc + '-streamUserList', 1, current_user.username)

        if requestedChannel.showChatJoinLeaveNotification:
            pictureLocation = current_user.pictureLocation
            if current_user.pictureLocation is None:
                pictureLocation = '/static/img/user2.png'
            else:
                pictureLocation = '/images/' + pictureLocation

            emit('message', {'user':'Server', 'msg': current_user.username + ' has left the room.', 'image': pictureLocation}, room=streamData['data'])
        else:
            if requestedChannel.showChatJoinLeaveNotification:
                emit('message', {'user':'Server', 'msg': 'Guest has left the room.', 'image': '/static/img/user2.png'}, room=streamData['data'])

    handle_viewer_total_request(streamData, room=streamData['data'])

    db.session.commit()
    db.session.close()
    return 'OK'

@socketio.on('openPopup')
def handle_new_popup_viewer(streamData):
    join_room(streamData['data'])
    return 'OK'

@socketio.on('closePopup')
def handle_leaving_popup_viewer(streamData):
    leave_room(streamData['data'])
    return 'OK'