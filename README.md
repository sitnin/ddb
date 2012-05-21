#Dumb .deb builder

Current version: 0.2.0

Project website: http://sitnin.github.com/ddb/

This is a python script which reads package description from a single JSON-file and creates binary package.

Rationale is very simple: this script doesn't compile or build anything. It just packs bunch of files (like your python or node.js website project) into a package.

##Installation

    $ echo "deb http://deb.sitnin.com/ ddb/" >> /etc/apt/sources.list
    $ apt-get update
    $ apt-get install ddb

## Building of the ddb package

I build ddb .deb package with ddb itself since the very first package. It's simple:

    $ ddb -r deb/deb.json -s ./ -o ./out -t ./tmp -u3 -f

And this is how is the output looks like:

    Dumb .deb builder version 0.1.0 (c) Gregory Sitnin, 2012.

    Source: /home/builder/ddb
    Output: /home/builder/ddb/out
    Temp: /home/builder/ddb/tmp
    Rules file /home/builder/ddb/deb/deb.json

    Copying files...
    Generating DEBIAN directory contents...
    Building package...
    dpkg-deb: building package `ddb' in `ddb_0.1.0-0ubuntu3_all.deb'.
    Building package...
    Deleting temporary directory...

    Package built: /home/builder/ddb/out/ddb_0.1.0-0ubuntu3_all.deb

## TODO

  * Python Virtualenv support (planned for 0.3)

## Contact information

Feel free to contact me about bugs, features and suggestions via:

  * Twitter: sitnin
  * Email: sitnin@gmail.com
