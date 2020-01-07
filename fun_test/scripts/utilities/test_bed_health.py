from lib.system.fun_test import *


test_bed_name = fun_test.get_custom_arg("test_bed_name")

fun_test.test_assert(test_bed_name, "Unable to determine test-bed name")

am = fun_test.get_asset_manager()
assets_in_test_bed = am.get_assets_required(test_bed_name=test_bed_name)

asset_health_map = {}

for asset_type, asset_names in assets_in_test_bed.iteritems():
    fun_test.log(asset_type)
    for asset_name in asset_names:
        instance = am.get_asset_instance_by_name(asset_type=asset_type, asset_name=asset_name)
        fun_test.test_assert(instance, "Get asset instance")
        health = instance.health(only_reachability=True)
        asset_health_map[asset_name] = health

fun_test.log_section("Health summary")
for asset_name, asset_health in asset_health_map.iteritems():
    fun_test.log("Asset: {}, Health: {}".format(asset_name, asset_health))