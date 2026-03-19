export default function ProductCard({ product }) {
  return (
    <div style={{border:"1px solid #ccc", padding:"8px", margin:"4px"}}>
      <h3>{product.name}</h3>
      <p>Brand: {product.brand}</p>
      <p>Price: ${product.price}</p>
      <p>Reason: {product.reason}</p>
    </div>
  );
}