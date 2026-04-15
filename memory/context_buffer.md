<!-- Last updated: 2026-04-15 16:19 UTC -->
e) {
            e.preventDefault();
            const request = requestInput.querySelector('textarea').value;
            socket.emit('submit_request', { content: request });
            requestInput.querySelector('textarea').value = '';
        });

        // Receive chat messages
        socket.on('chat_message', function(data) {
            const msgDiv = document.createElement('div');
            msgDiv.className = 'list-group-item';
            msgDiv.textContent = `${data.user}: ${data.message}`;
            document.getElementById('chat').appendChild(msgDiv);
            document.getElementById('chat').scrollTop = document.getElementById('chat').scrollHeight;
        });

        // Receive requests list
        socket.on('update_requests', function(data) {
            requestsList.innerHTML = '';
            data.forEach(req => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = req.content;
                const approveBtn = document.createElement('button');
                approveBtn.textContent = 'Approve';
                approveBtn.className = 'btn btn-sm btn-success mx-2';
                approveBtn.onclick = () => socket.emit('approve_request', { id: req.id });
                const denyBtn = document.createElement('button');
                denyBtn.textContent = 'Deny';
                denyBtn.className = 'btn btn-sm btn-danger';
                denyBtn.onclick = () => socket.emit('deny_request', { id: req.id });
                li.appendChild(approveBtn);
                li.appendChild(denyBtn);
                requestsList.appendChild(li);
            });
        });
    </script>
</body>
</html>
FILE_CONTENT_END

LIVE_CONTEXT_ADD: `index.html` template created with Bootstrap styling, chat interface, request submission form, and pending requests list. Next steps: implement approval/denial functionality for requests and ensure real-time updates via Socket.IO.