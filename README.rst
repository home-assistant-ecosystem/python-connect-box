python-connect-box
==================

Python Client for interacting with the cable modem/router Compal CH7465LG which
is provided under different names by various ISP in Europe.

- UPC Connect Box (CH)
- Irish Virgin Media Super Hub 3.0 (IE)
- Ziggo Connectbox (NL)
- Unitymedia Connect Box (DE)

This module is not official, developed, supported or endorsed by UPC, 
Unitymedia or Compal.

There is an interface with is providing details about various states like the
DHCP lease table for Ethernet and Wifi.

.. code:: xml

    <?xml version="1.0" encoding="UTF-8"?>
    <LanUserTable>
       <Ethernet>
          <clientinfo>
             <interface>Ethernet 2</interface>
             <IPv4Addr>192.168.0.160/24</IPv4Addr>
             <index>0</index>
             <interfaceid>2</interfaceid>
             <hostname>GW-B072BF27A983</hostname>
             <MACAddr>B0:72:BF:27:A9:83</MACAddr>
             <method>1</method>
             <leaseTime>00:00:34:53</leaseTime>
    ...

``connect_box`` is handling the retrieval of the data and the parsing. The 
primary use case is the `Home Assistant <https://home-assistant.io>`_
``upc_connect`` device tracker but one could use it in other projects as well.

Installation
------------

The module is available from the `Python Package Index <https://pypi.python.org/pypi>`_.

.. code:: bash

    $ pip3 install connect_box

Usage
-----

The file ``example.py`` contains an example about how to use this module.

Development
-----------

For development is recommended to use a ``venv``.

.. code:: bash

    $ python3.6 -m venv .
    $ source bin/activate
    $ python3 setup.py develop

License
-------

``connect_box`` is licensed under MIT, for more details check LICENSE.
