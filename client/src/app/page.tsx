// This is a Server Component by default in Next.js App Router
import UserSwitch from '@/components/ui/UserSwitch';

async function getRandomProduct() {
  const randomId = Math.floor(Math.random() * 13) + 1; // Adjust range based on your DB
  const res = await fetch(`http://127.0.0.1:8000/products/${randomId}`, {
    // Optional: disables caching for fresh fetch
    next: { revalidate: 0 },
    // Required for local development
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch product with ID ${randomId}`);
  }

  return res.json();
}

export default async function Home() {
  const product = await getRandomProduct();
  console.log(product)

  return (
    <div className="p-4 space-y-4">
      <div className="text-lg font-semibold">
        <UserSwitch
          initialOn={true}
          onLabel="You are a stinky stinker"
          offLabel="you are no longer a stinky stinker"
        />
      </div>

      <div className="mt-4">
        <h2 className="text-xl font-bold">🎁 Random Product</h2>
        <p><strong>Name:</strong> {product.item.product_name}</p>
        <p><strong>Price:</strong> ${product.item.price}</p>
        <p><strong>category:</strong> {product.item.category}</p>
      </div>
    </div>
  );
}