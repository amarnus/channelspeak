$(document).ready(function(context) {
  $('.chatAreaWrapper').scrollTo('max');
  formatMessage = function(author, message) {
		return '<div><strong>' + author.toLowerCase() + '</strong>: ' + message + '</div>';
	}
  $('#chatBox').ajaxForm({
		beforeSubmit: function(arr, $form, options) {
			for (var i in arr) {
				var arg = arr[i];
				if ('name' in arg && arg.name == 'message') {
					if (!arg.value.length) {
						return false; // Prevents empty messages from going through
					}
					$('#chatBox .inputBox').val(''); // Clears the input box after sending last post
					$('.chatArea').append(formatMessage('me', arg.value));
					$('.chatAreaWrapper').scrollTo('max'); // Scroll chat area to the end to see last post
				}
			}
		}
	});
  var channel = new goog.appengine.Channel(token);
  if (channel && channel !== undefined) {
    var socket = channel.open();
    socket.onopen = function() {
	    if (console) {
	     	console.log('Socket opened');
	    }
		};
		socket.onmessage = function(message) {
			if (console) {
			 	console.log('Packet received from the server');
			 	var data = JSON.parse(message.data);
			  if ('type' in data) {
					switch(data.type) {
						case 'arrived':
					    $('.members .content').append('<div>' + data.author.toLowerCase() + '</div>');
						  break;
						case 'message':
						  $('.chatArea').append(formatMessage(data.author, data.message));
						  $('.chatAreaWrapper').scrollTo('max'); // Scroll chat area to the end to see last post
						  break;
					}
				}
		  }
		};	
		socket.onerror = function(error) {
			if (console) { 
				console.log('There was an error receving a packet from the server');
			 	console.log(error);
			 	console.log(arguments);
			}
		}
		socket.onclose = function() {
			if (console) {
			 	console.log('Socket closed');
			 	console.log(arguments);
			}
		};
	}
});