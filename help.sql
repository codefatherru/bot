select * from p2q where poll_id=1 order by sequence limit 1 ;  /*выбрать первый вопрос опроса*/

select * from option where question_id = 1 and title = 'below than 50 000 $'; /*проверить ответли это на вопрос*/