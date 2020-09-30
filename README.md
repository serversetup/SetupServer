## Note: This project is no longer maintained. Better use [WordOps](https://wordops.net/)

#SimpleSetupServer

[![Build Status](https://travis-ci.org/serversetup/SetupServer.svg?branch=master)](https://travis-ci.org/serversetup/SetupServer)


**SimpleSetupServer currently supports:**
- Ubuntu 14.04


**Port Requirements:**

| Name  | Port Number | Inbound | Outbound  |
|:-----:|:-----------:|:-------:|:---------:|
|SSH    |22           | ✓       |✓          |
|HTTP    |80           | ✓       |✓          |
|HTTPS/SSL    |443           | ✓       |✓          |
|SSS Admin    |22222           | ✓       |          |
|GPG Key Server    |11371           |        |✓          |

## Quick Start

```bash
wget -qO sss bit.do/sssinstall && sudo bash sss     # Install Simple Setup Server
sudo sss site create example.com --mysql            # Install required packages & setup example.com
```

## License
[MIT](http://opensource.org/licenses/MIT)

[![forthebadge](http://forthebadge.com/images/badges/made-with-crayons.svg)](http://forthebadge.com)

