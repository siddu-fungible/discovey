if [ -d "fio" ]; then
    rm -rf ./fio
fi

if [ -f "fio" ]; then
    echo "fio is already present"
    exit -1
fi
git clone https://github.com/axboe/fio.git
cd fio
git checkout df4bf1178ed773986129da6038961388af926971
git apply ../../../fio-plugin/patch
mkdir -p Integration/tools/fio-plugin
cp ../../../../../Integration/tools/fio-plugin/* Integration/tools/fio-plugin/
make
cd ..
mv fio/fio fio_exe
rm -rf fio/
mv fio_exe fio
