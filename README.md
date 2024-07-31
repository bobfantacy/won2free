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
COMPUTE: AWS Lambda, 1 Million free requests per month
STORAGE: Amazon DynamoDB, 25 GB of storage
APP INTEGRATION： Amazon SQS 1 Million requests
SCHEDULE:  Amazon EventBridge Event buses All state change events published by AWS services by default are free

Only a free s3 storage will be used, s3 is cheep~~
