from redis import Redis
from rq import Queue
from app.tasks import count_words_at_url, send_verification_email

q = Queue(connection=Redis())


#result = q.enqueue(count_words_at_url, 'http://nvie.com')
result = q.enqueue(send_verification_email, 'kovach.aleksey19@ya.ru', 'Aleksey', 'qweqweqwe')


