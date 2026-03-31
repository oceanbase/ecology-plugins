# UniSelect Course Demo

**UniSelect Course** is a university course selection management system. Use it to manage course information, view course details, add and delete reviews, and edit course capacity.

Built with **Next.js**, **OceanBase Cloud** , and deployable on **Vercel**.

## Demo

![UniSelect Course screenshot](https://github.com/user-attachments/assets/d1fa46a9-cbe7-4b62-9015-f053da41ac5b)

**Live demo:** [Open the app](https://oceanbase-nextjs-vercel-demo.vercel.app) 

## Deploy to Vercel

You can deploy this demo with one click if you already have an OceanBase database (or create one after provisioning through [OceanBase Cloud](https://www.oceanbase.com/product/cloud)).

**Quick deployment**:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/sc-source/oceanbase-nextjs-vercel-demo&project-name=OceanBase%20Cloud%20Starter&repository-name=oceanbase-cloud-starter&integration-ids=oac_kzJzQ0seDkU8FXrt6cgoec48&demo-title=OceanBase%20Cloud%20Starter&demo-description=A%20university%20course%20selection%20management%20system%20built%20with%20Next.js%20and%20OceanBase&demo-url=https%3A%2F%2Foceanbase-nextjs-vercel-demo.vercel.app%2F&demo-image=https%3A%2F%2Fgithub.com%2Fuser-attachments%2Fassets%2Fd1fa46a9-cbe7-4b62-9015-f053da41ac5b)

## Local setup

### Install dependencies

```bash
npm install
```

### Environment

Copy the example env file and fill in your OceanBase connection string (from the [OceanBase Cloud console](https://www.oceanbase.com/product/cloud) → your cluster → connection info):

```bash
cp .env.example .env
```

```env
DATABASE_URL=mysql://<User>:<Password>@<Endpoint>:<Port>/<Database>
```

### Run the dev server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Learn more

- [OceanBase documentation](https://www.oceanbase.com/docs)
- [Vercel documentation](https://vercel.com/docs)
- [Next.js documentation](https://nextjs.org/docs)

## License

MIT
