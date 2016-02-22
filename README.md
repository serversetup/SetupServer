#SimpleSetupServer

**SimpleSetupServer currently supports:**
- Ubuntu 12.04 & 14.04


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
wget -qO sss bit.do/sssinstall && sudo bash sss     # Install easyengine 3
sudo sss site create example.com --mysql            # Install required packages & setup example.com
```

## License
[MIT](http://opensource.org/licenses/MIT)

[![forthebadge](http://forthebadge.com/images/badges/made-with-crayons.svg)](http://forthebadge.com)

