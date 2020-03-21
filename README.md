# anekdot_ru_crawler
## Crawler for [anekdot.ru](anekdot.ru) website.

It crawls the following categories:
`('anekdot', 'story', 'aphorism', 'poems')`.

### 1. Install requirements
```shell script
pip install -r requirements.txt
```

### 2. Run crawler
```shell script
cd scripts
python ./start_crawler.py --output_file=../data/parsed.txt --concurrency=25
```

It'll take about ~30 min to parse the whole website.
The final parsed text file structure is the following:

```text
anekdot, путин
[END_OF_UTTERANCE]
- Владимир Владимирович, а что случилось с галерой? - Она утонула...
[END_OF_DIALOG]
aphorism
[END_OF_UTTERANCE]
Обручальное кольцо - это символ змеи, хватающей себя за хвост.
[END_OF_DIALOG]
story
[END_OF_UTTERANCE]
Друг рассказал. Далее от его имени. "В нашем офисе есть лаборатория с дорогим оборудованием. Руководство ничего лучше не придумало, как сделать ОДИН ключ в лабу на весь офис. Нужно тебе в лабу, идешь к комнату с ключом, берешь его, идешь в лабу, поработал, далее в обратном порядке. И безусловно нашлась куча умников, которым в лом повесить ключ, а проще таскать его в кармане, пока остальные бегают с пеной у рта с вопросом "где ключ". Колбасило весь офис довольно долго, пока кто-то не придумал фишку. Взяли старый мобильник, активировали симку и присоединили к ключу. И сработало! Если ключа нет на месте, звонишь ему (ключу) и спрашиваешь ты где? Если он висит где ни попадя, тупо обходишь этажи офиса и слушаешь, где надрывается знакомая мелодия..."
[END_OF_DIALOG]
poems, овчарка
[END_OF_UTTERANCE]
Дети в подвале играли в бордель чести лишилась овчарка Адель
[END_OF_DIALOG]
```
It's not the most convenient structure for this type of data, but it was useful
for my personal purposes.

Each item (anekdot, story, poem or aphorism) covers 4 lines:
- `anekdot, путин` - tags sequence
- `[END_OF_UTTERANCE]` - end of tags line separator
- `- Владимир Владимирович, а что случилось с галерой? - Она утонула...` - the actual item text
- `[END_OF_DIALOG]` - end of item separator.

Note that, all whitespace symbols are replaced with one space symbol. So, there are no
any new line ot tabulation symbols in the data.