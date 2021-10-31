
socket.on('connect', function () {
    socket.emit('getUpvoteTotal', {loc: '{{video.id}}', vidType: 'video'});
});

setInterval(function () {
    socket.emit('getUpvoteTotal', {loc: '{{video.id}}', vidType: 'video'});
}, 30000);



socket.on('upvoteTotalResponse', function (msg) {

    if (msg['type'] === 'video') {
        upvoteDivID = 'totalUpvotes';
        upvoteIconID = 'upVoteIcon';
        upvoteButtonID = 'upvoteButton';
    } else if (msg['type'] === 'comment') {
        upvoteDivID = 'upvoteTotalComments-' + msg['loc'];
        upvoteIconID = 'commentUpvoteIcon-' + msg['loc'];
        upvoteButtonID = 'commentUpvoteButton-' + msg['loc'];
    }

    document.getElementById(upvoteDivID).innerHTML = msg['totalUpvotes'];
    document.getElementById(upvoteDivID + 'Mobile').innerHTML = msg['totalUpvotes'];

    if (msg['myUpvote'] === 'True') {
        if (document.getElementById(upvoteIconID).classList.contains('far')) {
        document.getElementById(upvoteIconID).classList.remove('far');
        document.getElementById(upvoteIconID).classList.add('fas');
    }
    if (document.getElementById(upvoteButtonID).classList.contains('btn-outline-success')) {
        document.getElementById(upvoteButtonID).classList.remove('btn-outline-success');
        document.getElementById(upvoteButtonID).classList.add('btn-success');
    }
    if (msg['type'] === 'video') {
        if (document.getElementById(upvoteIconID + 'Mobile').classList.contains('far')) {
            document.getElementById(upvoteIconID + 'Mobile').classList.remove('far');
            document.getElementById(upvoteIconID + 'Mobile').classList.add('fas');
        }

        if (document.getElementById(upvoteButtonID + 'Mobile').classList.contains('btn-outline-success')) {
            document.getElementById(upvoteButtonID + 'Mobile').classList.remove('btn-outline-success');
            document.getElementById(upvoteButtonID + 'Mobile').classList.add('btn-success');
        }
    }
    } else if (msg['myUpvote'] === 'False') {
        if (document.getElementById(upvoteIconID).classList.contains('fas')) {
            document.getElementById(upvoteIconID).classList.remove('fas');
            document.getElementById(upvoteIconID).classList.add('far');
        }
        if (document.getElementById(upvoteButtonID).classList.contains('btn-success')) {
            document.getElementById(upvoteButtonID).classList.remove('btn-success');
            document.getElementById(upvoteButtonID).classList.add('btn-outline-success');
        }

        if (msg['type'] === 'video') {
            if (document.getElementById(upvoteIconID + 'Mobile').classList.contains('fas')) {
                document.getElementById(upvoteIconID + 'Mobile').classList.remove('fas');
                document.getElementById(upvoteIconID + 'Mobile').classList.add('far');
            }
            if (document.getElementById(upvoteButtonID + 'Mobile').classList.contains('btn-success')) {
                document.getElementById(upvoteButtonID + 'Mobile').classList.remove('btn-success');
                document.getElementById(upvoteButtonID + 'Mobile').classList.add('btn-outline-success');
            }
        }
    }
});

function changeUpvote(type, id) {
    socket.emit('changeUpvote', {loc: id, vidType: type});
    socket.emit('getUpvoteTotal', {loc: id, vidType: type});
}