# Quix Clickstream Analysis Template

Welcome to the Quix Clickstream Analysis Template! This repository provides a template for leveraging the power of the Quix platform to perform real-time clickstream analysis. With this template, you can see how to detect and trigger events dynamically based on real-time analysis of click behavior.

 - See the deployed projects [front end](https://demo-webshop-frontend-demo-clickstreamanalysis-prod.deployments.quix.io) and [dashboard](https://streamlit-dashboard-demo-clickstreamanalysis-prod.deployments.quix.io/?_ga=2.101880327.729325520.1700470040-1544698923.1686060578)
 - [See the project running in Quix](https://portal.platform.quix.io/?token=pat-b88b3caf912641a1b0fa8b47b262868b)

## Features

- **Real-time analysis:** The template empowers you to analyze user clickstreams in real time, allowing you to gain immediate insights into how users interact with your website or application.

- **Quix platform integration:** This template is designed to seamlessly integrate with the Quix platform. Quix provides a user-friendly environment for managing and analyzing data, making it an ideal choice for real-time clickstream analysis.

- **Custom built front end:** We have built a front end in the form of a web store. This simple shop allows the user to select their age and gender and click through to products in several different categories.

- **Real-time dashboard:** We have built a real-time dashboard using Streamlit and connected it to Quix using Redis.

## Getting Started

To get started with the Quix Clickstream Analysis Template, follow these steps:

1. **Fork this Repository:** Start by forking this repository to your GitHub account. This will create a copy of the template that you can customize and adapt to your specific needs.

2. **Configure Quix:** Connect the template to your Quix account and configure the necessary settings. Check out the docs for step-by-step instructions to guide you through the setup process. (*coming soon*)

## Technologies used

Some of the technologies used by this template project are listed here.

**Infrastructure:** 

* [Quix](https://quix.io/)
* [Docker](https://www.docker.com/)
* [Kubernetes](https://kubernetes.io/)

**Backend:** 

* [Redpanda Cloud](https://redpanda.com/redpanda-cloud)
* [Redis Cloud](https://redis.io/)
* [Quix Streams](https://github.com/quixio/quix-streams)
* [pandas](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)

**Frontend:**

* [Angular](https://angular.io/)
* [Streamlit](https://streamlit.io/)
* [Microsoft SignalR](https://learn.microsoft.com/en-us/aspnet/signalr/)

**Data warehousing:**

* [Snowplow](https://snowplow.io/)
  
## Documentation

A tutorial will soon be published on our docs on how to fork and set this template up in your Quix cloud environment.

Start exploring the world of real-time clickstream analysis with Quix today! Feel free to contribute, report issues, or share your experiences with the [Quix Community](https://join.slack.com/t/stream-processing/shared_invite/zt-26z0j0rmc-ErYLXaGVa4OaKGagznSjlw). Happy clicking!
