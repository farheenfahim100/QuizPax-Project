#!/bin/bash

exec gunicorn project:app \
  --worker-class gevent \
  --workers 1 \
<<<<<<< HEAD
  --bind 0.0.0.0:$PORT
=======
  --bind 0.0.0.0:$PORT
>>>>>>> 7600fff25f82c5fa95e4544d75b78ed57b388aa0
