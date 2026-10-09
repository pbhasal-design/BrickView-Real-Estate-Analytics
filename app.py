import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="BrickView",
    page_icon="🏠",
    layout="wide"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

DB_PATH = "brickview.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


# =========================================================
# TABLE INFORMATION
# =========================================================

TABLE_KEYS = {
    "buyers": "buyer_id",
    "listings": "listing_id",
    "property_attributes": "attribute_id",
    "agents": "agent_id",
    "sales": "listing_id"
}


TABLES = [
    "buyers",
    "listings",
    "property_attributes",
    "agents",
    "sales"
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_columns(table_name):

    conn = get_connection()

    schema = pd.read_sql_query(
        f"PRAGMA table_info({table_name})",
        conn
    )

    conn.close()

    return schema


def get_data(table_name):

    conn = get_connection()

    df = pd.read_sql_query(
        f"SELECT * FROM {table_name}",
        conn
    )

    conn.close()

    return df


# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

st.sidebar.title("🏠 BrickView")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🛠️ CRUD Operations"
    ]
)


# =========================================================
# DASHBOARD PAGE
# =========================================================

if page == "📊 Dashboard":

    st.title("🏠 BrickView Real Estate Analytics Platform")

    # =====================================================
    # LOAD LISTINGS
    # =====================================================

    try:

        conn = get_connection()

        df = pd.read_sql_query(
            "SELECT * FROM listings",
            conn
        )

        conn.close()

    except Exception as e:

        st.error(f"Database error: {e}")
        st.stop()


    # =====================================================
    # CONVERT DATE
    # =====================================================

    df["date_listed"] = pd.to_datetime(
        df["date_listed"],
        errors="coerce"
    )


    # =====================================================
    # SIDEBAR FILTERS
    # =====================================================

    st.sidebar.header("🔎 Filters")

    cities = sorted(
        df["city"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_cities = st.sidebar.multiselect(
        "Select City",
        cities,
        default=cities
    )


    property_types = sorted(
        df["property_type"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_property_type = st.sidebar.selectbox(
        "Property Type",
        ["All"] + property_types
    )


    # =====================================================
    # PRICE FILTER
    # =====================================================

    min_price = int(
        df["price"].min()
    )

    max_price = int(
        df["price"].max()
    )

    selected_price = st.sidebar.slider(
        "Price Range",
        min_price,
        max_price,
        (min_price, max_price)
    )


    # =====================================================
    # APPLY FILTERS
    # =====================================================

    filtered_df = df.copy()


    # City filter

    if selected_cities:

        filtered_df = filtered_df[
            filtered_df["city"].isin(selected_cities)
        ]


    # Property type filter

    if selected_property_type != "All":

        filtered_df = filtered_df[
            filtered_df["property_type"]
            == selected_property_type
        ]


    # Price filter

    filtered_df = filtered_df[
        (filtered_df["price"] >= selected_price[0])
        &
        (filtered_df["price"] <= selected_price[1])
    ]


    # =====================================================
    # KPI CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)


    col1.metric(
        "🏠 Total Listings",
        len(filtered_df)
    )


    col2.metric(
        "💰 Average Price",
        f"{filtered_df['price'].mean():,.0f}"
        if len(filtered_df) > 0
        else "0"
    )


    col3.metric(
        "📐 Average Sqft",
        f"{filtered_df['sqft'].mean():,.0f}"
        if len(filtered_df) > 0
        else "0"
    )


    col4.metric(
        "🏙️ Cities",
        filtered_df["city"].nunique()
    )


    # =====================================================
    # MAP
    # =====================================================

    st.subheader("📍 Property Listings Map")

    map_df = filtered_df.dropna(
        subset=[
            "latitude",
            "longitude"
        ]
    )


    if len(map_df) > 0:

        fig_map = px.scatter_map(
            map_df,
            lat="latitude",
            lon="longitude",
            hover_name="listing_id",
            hover_data=[
                "city",
                "property_type",
                "price",
                "sqft"
            ],
            zoom=4,
            height=500
        )

        st.plotly_chart(
            fig_map,
            use_container_width=True
        )

    else:

        st.info(
            "No location data available."
        )


    # =====================================================
    # BAR CHART + PIE CHART SIDE BY SIDE
    # =====================================================

    col1, col2 = st.columns(2)


    # =====================================================
    # BAR CHART - LEFT
    # =====================================================

    with col1:

        st.subheader(
            "📊 Listings by City"
        )

        city_count = (
            filtered_df
            .groupby("city")
            .size()
            .reset_index(name="Listings")
            .sort_values(
                "Listings",
                ascending=False
            )
        )


        fig_bar = px.bar(
            city_count,
            x="city",
            y="Listings",
            title="Number of Listings by City"
        )


        st.plotly_chart(
            fig_bar,
            use_container_width=True
        )


    # =====================================================
    # PIE CHART - RIGHT
    # =====================================================

    with col2:

        st.subheader(
            "🏠 Property Type Distribution"
        )

        property_count = (
            filtered_df["property_type"]
            .value_counts()
            .reset_index()
        )


        property_count.columns = [
            "Property Type",
            "Listings"
        ]


        fig_pie = px.pie(
            property_count,
            names="Property Type",
            values="Listings",
            title="Property Type Distribution"
        )


        st.plotly_chart(
            fig_pie,
            use_container_width=True
        )


    # =====================================================
    # MONTHLY TREND
    # =====================================================

    st.subheader(
        "📈 Monthly Listings Trend"
    )


    trend_df = filtered_df.copy()


    trend_df["Month"] = (
        trend_df["date_listed"]
        .dt.to_period("M")
        .astype(str)
    )


    monthly = (
        trend_df
        .groupby("Month")
        .size()
        .reset_index(name="Listings")
    )


    fig_line = px.line(
        monthly,
        x="Month",
        y="Listings",
        markers=True,
        title="Monthly Listings"
    )


    st.plotly_chart(
        fig_line,
        use_container_width=True
    )


    # =====================================================
    # DATA TABLE
    # =====================================================

    st.subheader(
        "📋 Listing Details"
    )


    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# CRUD PAGE
# =========================================================

elif page == "🛠️ CRUD Operations":

    st.title(
        "🛠️ CRUD Operations"
    )

    st.write(
        "Create, Read, Update and Delete records "
        "from the BrickView database."
    )


    # =====================================================
    # SELECT TABLE
    # =====================================================

    selected_table = st.selectbox(
        "Select Database Table",
        TABLES
    )


    key_column = TABLE_KEYS[
        selected_table
    ]


    st.info(
        f"Selected table: **{selected_table}**  |  "
        f"Record identifier: **{key_column}**"
    )


    # =====================================================
    # GET TABLE DATA
    # =====================================================

    data = get_data(
        selected_table
    )

    schema = get_columns(
        selected_table
    )


    # =====================================================
    # CRUD TABS
    # =====================================================

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "👁️ View Records",
            "➕ Add Record",
            "✏️ Update Record",
            "🗑️ Delete Record"
        ]
    )


    # =====================================================
    # READ
    # =====================================================

    with tab1:

        st.subheader(
            f"View {selected_table} Records"
        )


        if len(data) == 0:

            st.warning(
                "No records found."
            )

        else:

            page_size = st.selectbox(
                "Records per page",
                [10, 25, 50, 100],
                key="view_page_size"
            )


            total_records = len(data)


            total_pages = max(
                1,
                (
                    total_records
                    + page_size
                    - 1
                )
                // page_size
            )


            current_page = st.number_input(
                "Page Number",
                min_value=1,
                max_value=total_pages,
                value=1,
                step=1
            )


            start = (
                current_page - 1
            ) * page_size


            end = start + page_size


            st.dataframe(
                data.iloc[start:end],
                use_container_width=True,
                hide_index=True
            )


            st.write(
                f"Page {current_page} of "
                f"{total_pages} | "
                f"Total Records: "
                f"{total_records}"
            )


    # =====================================================
    # CREATE
    # =====================================================

    with tab2:

        st.subheader(
            f"Add New {selected_table} Record"
        )


        with st.form(
            f"add_form_{selected_table}"
        ):

            values = {}


            for _, column in schema.iterrows():

                column_name = column["name"]

                column_type = column["type"]


                # Integer identifier
                # is entered manually

                if (
                    column_name == key_column
                    and column_type.upper()
                    == "INTEGER"
                ):

                    continue


                if column_type.upper() == "INTEGER":

                    values[
                        column_name
                    ] = st.number_input(
                        column_name,
                        value=0,
                        step=1
                    )


                elif column_type.upper() == "REAL":

                    values[
                        column_name
                    ] = st.number_input(
                        column_name,
                        value=0.0
                    )


                else:

                    values[
                        column_name
                    ] = st.text_input(
                        column_name
                    )


            submitted = st.form_submit_button(
                "➕ Add Record"
            )


            if submitted:

                try:

                    columns = list(
                        values.keys()
                    )


                    placeholders = ", ".join(
                        ["?"] * len(columns)
                    )


                    column_string = ", ".join(
                        columns
                    )


                    sql = f"""
                    INSERT INTO {selected_table}
                    ({column_string})
                    VALUES ({placeholders})
                    """


                    conn = get_connection()


                    conn.execute(
                        sql,
                        list(
                            values.values()
                        )
                    )


                    conn.commit()

                    conn.close()


                    st.success(
                        "Record added successfully!"
                    )


                    st.rerun()


                except Exception as e:

                    st.error(
                        f"Unable to add record: {e}"
                    )


    # =====================================================
    # UPDATE
    # =====================================================

    with tab3:

        st.subheader(
            f"Update {selected_table} Record"
        )


        if len(data) == 0:

            st.warning(
                "No records available for update."
            )

        else:

            record_ids = (
                data[key_column]
                .dropna()
                .astype(str)
                .tolist()
            )


            selected_id = st.selectbox(
                f"Select {key_column}",
                record_ids,
                key=f"update_id_{selected_table}"
            )


            selected_record = data[
                data[key_column].astype(str)
                == selected_id
            ].iloc[0]


            with st.form(
                f"update_form_{selected_table}"
            ):

                updated_values = {}


                for _, column in schema.iterrows():

                    column_name = column["name"]

                    column_type = column["type"]


                    current_value = (
                        selected_record[
                            column_name
                        ]
                    )


                    if column_name == key_column:

                        st.text_input(
                            column_name,
                            value=str(
                                current_value
                            ),
                            disabled=True
                        )

                        continue


                    if column_type.upper() == "INTEGER":

                        try:

                            default_value = int(
                                current_value
                            )

                        except:

                            default_value = 0


                        updated_values[
                            column_name
                        ] = st.number_input(
                            column_name,
                            value=default_value,
                            step=1
                        )


                    elif column_type.upper() == "REAL":

                        try:

                            default_value = float(
                                current_value
                            )

                        except:

                            default_value = 0.0


                        updated_values[
                            column_name
                        ] = st.number_input(
                            column_name,
                            value=default_value
                        )


                    else:

                        if pd.isna(
                            current_value
                        ):

                            current_value = ""


                        updated_values[
                            column_name
                        ] = st.text_input(
                            column_name,
                            value=str(
                                current_value
                            )
                        )


                update_button = (
                    st.form_submit_button(
                        "💾 Update Record"
                    )
                )


                if update_button:

                    try:

                        set_clause = ", ".join(
                            [
                                f"{col} = ?"
                                for col
                                in updated_values.keys()
                            ]
                        )


                        sql = f"""
                        UPDATE {selected_table}
                        SET {set_clause}
                        WHERE {key_column} = ?
                        """


                        parameters = list(
                            updated_values.values()
                        )


                        parameters.append(
                            selected_id
                        )


                        conn = get_connection()


                        conn.execute(
                            sql,
                            parameters
                        )


                        conn.commit()

                        conn.close()


                        st.success(
                            "Record updated successfully!"
                        )


                        st.rerun()


                    except Exception as e:

                        st.error(
                            f"Unable to update record: {e}"
                        )


    # =====================================================
    # DELETE
    # =====================================================

    with tab4:

        st.subheader(
            f"Delete {selected_table} Record"
        )


        if len(data) == 0:

            st.warning(
                "No records available for deletion."
            )

        else:

            record_ids = (
                data[key_column]
                .dropna()
                .astype(str)
                .tolist()
            )


            delete_id = st.selectbox(
                f"Select {key_column} to delete",
                record_ids,
                key=f"delete_id_{selected_table}"
            )


            selected_delete_record = data[
                data[key_column].astype(str)
                == delete_id
            ]


            st.write(
                "Record selected for deletion:"
            )


            st.dataframe(
                selected_delete_record,
                use_container_width=True,
                hide_index=True
            )


            confirm_delete = st.checkbox(
                "I confirm that I want to delete this record."
            )


            if st.button(
                "🗑️ Delete Record",
                type="primary"
            ):

                if not confirm_delete:

                    st.warning(
                        "Please confirm deletion first."
                    )

                else:

                    try:

                        sql = f"""
                        DELETE FROM {selected_table}
                        WHERE {key_column} = ?
                        """


                        conn = get_connection()


                        conn.execute(
                            sql,
                            (delete_id,)
                        )


                        conn.commit()

                        conn.close()


                        st.success(
                            "Record deleted successfully!"
                        )


                        st.rerun()


                    except Exception as e:

                        st.error(
                            f"Unable to delete record: {e}"
                        )