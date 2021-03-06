from typing import Dict

from pyspark.sql import SparkSession, Column, DataFrame
from pyspark.sql.functions import array
# noinspection PyUnresolvedReferences
from pyspark.sql.functions import lit

from spark_auto_mapper.automappers.automapper import AutoMapper
from spark_auto_mapper.data_types.list import AutoMapperList
from spark_auto_mapper.helpers.spark_higher_order_functions import filter


def test_auto_mapper_array_multiple_items_with_null(
    spark_session: SparkSession
) -> None:
    # Arrange
    spark_session.createDataFrame(
        [
            (1, 'Qureshi', 'Imran'),
            (2, 'Vidal', 'Michael'),
        ], ['member_id', 'last_name', 'first_name']
    ).createOrReplaceTempView("patients")

    source_df: DataFrame = spark_session.table("patients")

    df: DataFrame = source_df.select("member_id")
    df.createOrReplaceTempView("members")

    # Act
    mapper = AutoMapper(
        view="members",
        source_view="patients",
        keys=["member_id"],
        drop_key_columns=False
    ).columns(dst2=AutoMapperList(["address1", "address2", None]))

    assert isinstance(mapper, AutoMapper)
    sql_expressions: Dict[str, Column] = mapper.get_column_specs(
        source_df=source_df
    )
    for column_name, sql_expression in sql_expressions.items():
        print(f"{column_name}: {sql_expression}")

    assert str(sql_expressions["dst2"]) == str(
        filter(
            array(lit("address1"), lit("address2"), lit(None)),
            lambda x: x.isNotNull()
        ).alias("dst2")
    )

    result_df: DataFrame = mapper.transform(df=df)

    # Assert
    result_df.printSchema()
    result_df.show()

    assert result_df.where("member_id == 1"
                           ).select("dst2").collect()[0][0][0] == "address1"
    assert result_df.where("member_id == 1"
                           ).select("dst2").collect()[0][0][1] == "address2"
    assert result_df.where("member_id == 2"
                           ).select("dst2").collect()[0][0][0] == "address1"
    assert result_df.where("member_id == 2"
                           ).select("dst2").collect()[0][0][1] == "address2"
