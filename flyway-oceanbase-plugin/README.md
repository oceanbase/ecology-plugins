# Flyway-oceanbase-plugin

This plugin enables Flyway to support OceanBase in both MySQL and Oracle compatibility modes.

Flyway is a powerful database migration tool, supporting both MySQL and Oracle modes. This plugin ensures compatibility between Flyway and OceanBase in **MySQL mode**, while also supporting database migrations in **Oracle mode**.

------

## 🧩 Project Overview

This project addresses issues encountered by developers using **Flyway** for database migrations in **OceanBase's MySQL mode**, while also enabling support for **OceanBase's Oracle mode**.

------

## ✅ Resolved Issues

| **Issue**                      | **Description**                                              | **Solution**                                                 |
| ------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `version` Column Conflict      | Repeatable migration (`R` script) fails on first insertion due to `version = NULL`. | Automatically modifies `flyway_schema_history` to allow `version VARCHAR(50) NULL`. |
| Missing Baseline Configuration | Flyway fails to recognize existing databases.                | Sets `baseline-on-migrate=true` and `baseline-version=1.0`.  |
| Driver Compatibility           | Uses native MySQL driver.                                    | Replaced with OceanBase-specific driver `flyway-database-oceanbase-10.16.1.jar`. |
| Oracle Mode Support            | Oracle mode requires special handling.                       | Uses OceanBase-specific driver `flyway-database-oceanbase-10.16.1.jar`. |

------

## 🛠️ Features

- ✅ **Automatic Schema Fix**:
  Detects and modifies the `flyway_schema_history` table to allow `NULL` in the `version` column.
- ✅ **Baseline Configuration**:
  Ensures compatibility with existing databases via `baseline-on-migrate=true` and `baseline-version=1.0`.
- ✅ **OceanBase Driver Integration**:
  Uses a custom Flyway driver (`flyway-database-oceanbase-10.16.1.jar`) optimized for OceanBase.
- ✅ **No Code Changes Required**:
  Seamlessly integrates with existing Flyway scripts and configurations.

------

## 📦 Installation & Configuration

### 📌 Prerequisites

- Flyway version ≥ **10.8.1**
- Java 17 or higher

------

### 🛠️ Configuration Steps

#### 1. Modify `flyway_schema_history` Table Structure

Ensure the `version` column allows `NULL`:

```sql
-- If the table does not exist, create it
CREATE TABLE flyway_schema_history (
    installed_rank INT NOT NULL,
    version VARCHAR(50) NULL,  -- ✅ Allow NULL
    description VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL,
    script VARCHAR(1000) NOT NULL,
    checksum INT,
    installed_by VARCHAR(100) NOT NULL,
    installed_on TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_time INT NOT NULL,
    success BOOLEAN NOT NULL,
    PRIMARY KEY (installed_rank)
) ENGINE=InnoDB;

-- If the table exists, modify the column
ALTER TABLE flyway_schema_history MODIFY version VARCHAR(50) NULL;
```

⚠️ **Important**: In Oracle mode, no changes are required since `flyway_schema_history` is created by `flyway-core`. For MySQL mode, ensure the `version` column is `NULL` if using `R` scripts.

#### 2. Configure Flyway Parameters

Add the following to `application.properties` or `application.yml`:

```properties
# application.properties
spring.flyway.baseline-on-migrate=true
spring.flyway.baseline-version=1.0
```

```yaml
# application.yml
spring:
  flyway:
    baseline-on-migrate: true
    baseline-version: 1.0
```

#### 3. Replace Flyway Driver

Update `pom.xml` to use the OceanBase-specific driver:

```xml
<dependency>
    <groupId>org.flywaydb</groupId>
    <artifactId>flyway-database-oceanbase</artifactId>
    <version>10.16.1</version>
    <scope>system</scope>
    <systemPath>${project.basedir}/src/main/resources/lib/flyway-database-oceanbase-10.16.1.jar</systemPath>
</dependency>
```

📁 Place `flyway-database-oceanbase-10.16.1.jar` in the `src/main/resources/lib/` directory.

#### 4. Database Connection Configuration

Configure OceanBase MySQL mode connection:

```properties
# application.properties
spring.datasource.url=jdbc:oceanbase://<host>:<port>/<database>?obcompatibility=MYSQL
spring.datasource.username=<user>
spring.datasource.password=<password>
spring.flyway.enabled=true
yaml
```

```yaml
# application.yml
spring:
  datasource:
    url: jdbc:oceanbase://<host>:<port>/<database>?obcompatibility=MYSQL
    username: <user>
    password: <password>
  flyway:
    enabled: true
```

📌 **Parameter Explanation**:

- `obcompatibility=MYSQL`: Enables OceanBase's MySQL mode.
- `spring.flyway.enabled=true`: Enables Flyway automatic migration.

------

## 🧪 Example Migration Scripts

### 1. Versioned Migration Script (V prefix)

```sql
-- V1__create_users_table.sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NULL
);
```

### 2. Repeatable Migration Script (R prefix)

```sql
-- R__refresh_views.sql
CREATE OR REPLACE VIEW user_summary AS
SELECT id, name FROM users;
```

------

## ❓ Common Issues & Solutions

### Q1: Error `Cannot insert NULL into column 'version'` when executing R scripts?

**A1: Solution**

1. Ensure the `flyway_schema_history` table's `version` column allows `NULL`:

```sql
ALTER TABLE flyway_schema_history MODIFY version VARCHAR(50) NULL;
```

1. Set `baseline-on-migrate` and `baseline-version` parameters.

------

### Q2: How to verify Flyway is working properly?

**A2: Run the following command to check migration status:**

```bash
./flyway info -X -configFiles=conf/my.conf
```

------

## 📁 Project Structure Example

```plain
your-project/
├── src/
│   └── main/
│       ├── resources/
│       │   ├── db/migration/
│       │   │   ├── V1__create_users_table.sql
│       │   │   └── R__refresh_views.sql
│       │   └── lib/
│       │       └── flyway-database-oceanbase-10.16.1.jar
│       └── application.properties
├── pom.xml
└── README.md
```

------

## 📚 References

- [Flyway Official Documentation](https://flywaydb.org/)
- [OceanBase Official Documentation](https://oceanbase.com/)
- [Flyway & OceanBase Compatibility PR](https://github.com/flyway/flyway-community-db-support/pull/60)

------

## 📬 Contributing & Feedback

We welcome issues and pull requests to improve this project. For questions or suggestions, visit [GitHub Issues](https://github.com/oceanbase/ecology-plugins/issues).

------

## 📄 License

This project is licensed under the [Apache License 2.0](https://github.com/oceanbase/ecology-plugins/LICENSE).

------

Through this plugin, Flyway can seamlessly operate in OceanBase's MySQL mode, resolving issues with repeatable migrations (`R` scripts) and ensuring compatibility across both MySQL and Oracle modes.
