export { auth as proxy } from "@/auth";

export const config = {
  // Every page except the sign-in page, Auth.js's own routes, and static files.
  matcher: ["/((?!signin|api/auth|_next/static|_next/image|favicon.ico).*)"],
};
