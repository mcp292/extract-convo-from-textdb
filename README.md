Run [this script](extract_convo_from_textdb.py) to extract messages into a properly named .txt file for printing or emailing.

```
python3  extract_convo_from_textdb.py --help
```

For help locating and extracting the database in the first place check out [this SO post](https://android.stackexchange.com/questions/241439/how-to-access-texts-on-rooted-android-device-from-terminal).

[schema.txt](schema.txt) is not needed, but is included in case your database schema differs from mine and you need to dive into the code and make changes. Observing the foreign keys in the schema helped tremendously. You can see what I did based on my schema and adapt.
