# dbdmtwitterdetection

To detect events, go the `detection` folder an run:
`python3 main.py <input_file> <?output_file>`

`input_file` should be in CSV format with fields:
`id|timestampMS|geo_lat|geo_lon|user_id|userScreenName|place_fullname|place_bounding|hashtags|userMentions|text`

Then show the results by loading `index.html` (the output file of the python code must be located
at `detection/data.js`). Or just load directly `index.html` which will show our results on our dataset.
