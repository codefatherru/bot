select * from p2q where poll_id=1 order by sequence limit 1 ;  /*выбрать первый вопрос опроса*/

select * from option where question_id = 1 and title = 'below than 50 000 $'; /*проверить ответли это на вопрос*/

select * from p2q where poll_id=1 and sequence >1 order by sequence limit 1 ;  /*выбрать следующий вопрос опроса*/

select "'"||o1.id ||'-'|| o2.id ||'-'|| o3.id||"':"
 from option o1,  option o2,  option o3
 where
 o1.question_id = 1 and
 o2.question_id = 2 and
 o3.question_id = 3 
 order by
 o1.id, o2.id, o3.id; /* генератор вариантов для ответов */
 

select "'"||o1.id ||'-'|| o2.id ||"':"
 from option o1,  option o2
 where
 o1.question_id = 4 and
 o2.question_id = 5 
 order by
 o1.id, o2.id; /* генератор вариантов для ответов */
  