# TreasureHunt
CS249 project

## Testing Locally:
To test the zookeeper server locally, navigate to the dockerfiles folder and run the container to start the zookeeper server and test multiple clients to connect to the game.

## Installing dependencies:
Create a virtual env and activate it using the following commands:
```bash
cd gameWebsite
python3 -m venv .env
source .env/bin/activate
```
You should now see the terminal show (.env), now install the dependencies:
```bash
pip install -r requirements.txt
```
## Running the application
```bash
python app.py
```

## License

[MIT](https://choosealicense.com/licenses/mit/)