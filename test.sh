#!/bin/bash
beg=0
end=6
echo $((RANDOM % ($end - $beg ) + $beg))
