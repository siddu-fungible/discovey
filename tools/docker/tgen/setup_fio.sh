if [ -d "fio" ]; then
    rm -rf ./fio
fi

git clone https://github.com/axboe/fio.git
cd fio
git checkout df4bf1178ed773986129da6038961388af926971
git apply ../../../fio-plugin/patch
mkdir -p Integration/tools/fio-plugin
cp -r ../../../fio-plugin/* Integration/tools/fio-plugin/
