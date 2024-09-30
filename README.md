# Won2Free
Won2Free is a free funding bot, available for free access and deployment, designed to grant you financial freedom.

# Initiative
Luckily, I found Bitfinex in 2023. After several months of funding attempts, I discovered that the Lending Pro function doesn't work well for me. I noticed that most Bitfinex bots are not free. Since I happen to know a bit of coding, I thought I could use my skills to create bot. So, I decided to code my own bot to place my funding offers. This bot seems to work better than Lending Pro after months of practice.
Now, I want to make this bot public. I named the bot "Won2Free". I believe the name describes the blueprint of the bot.

1. "Won2Free" sounds like "123", conveying simplicity and ease of use.
2. The code is public and free to access. You are welcome to modify and improve it. 
3. The bot can be deployed to AWS Cloud utilizing the free tier resources of AWS, making it costless.

The most important thing is that you own the code and deploy it to your own AWS account. You have full control over security.
The code will be audited by everybody.

So let's get started.

# Free Architect
I will try my best to utilize the free tier of AWS resources, below are the resrouces:
```
COMPUTE: AWS Lambda, 1 Million free requests per month
STORAGE: Amazon DynamoDB, 25 GB of storage
APP INTEGRATION： Amazon SQS 1 Million requests
SCHEDULE:  Amazon EventBridge Event buses All state change events published by AWS services by default are free
```
What's more, a little s3 storage is needed. S3 is cheep ~~

# Installation

## Requirements
* A AWS key configured locally, see [here](https://serverless.com/framework/docs/providers/aws/guide/credentials/).
* A Telegram account.

```
Get a bot from Telegram, sending this message to @BotFather
/newbot
```
Markwon your own tgbot token.

## Tooling
* Node.js 20
Follow the [Instruction](https://nodejs.org/en/download/package-manager) to install Node.js 20
* Install Serverless framework
```
npm install serverless -g
```

## Deploy the base layers
A base layers had been created to booster the deploy and test in the development cycle. 
``` shell
$ cd layers
$ npm install 
$ sls deploy
Deploying "won2free-layers" to stage "dev" (ap-east-1)
✔ Service deployed to stack won2free-layers-prod (29s)
layers:
  pythonRequirements: arn:aws:lambda:ap-east-1:xxxxxxxxxx:layer:won2free-python-requirements:1
```
Mark down the version number tailing the won2free-python-requirements if it's not 1.

## Deploy Won2Free Bot

``` shell
$ cd ../src
# Copy the serverless.env.example.yml to serverless.env.yml
$ cp serverless.env.example.yml serverless.env.yml
# Put the token received into a file called serverless.env.yml, like this
TG_TOKEN: <your_token>
# Double Check the layer_name is the same as your just deployed.
LAYER_NAME: won2free-python-requirements:1
# And the other variables just keep them as default
# Deploy it!
$ serverless deploy -s prod
```

# References:
* https://github.com/keithrozario/Klayers