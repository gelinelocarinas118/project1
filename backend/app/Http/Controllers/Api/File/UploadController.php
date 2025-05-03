<?php

namespace App\Http\Controllers\api\file;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class UploadController extends Controller
{

public function storeMultiple(Request $request)
{
    if (!$request->hasFile('images')) {
        return response()->json(['error' => 'No images uploaded.'], 400);
    }

    $timestamp = now()->format('Ymd_His');
    $folder = "uploads/{$timestamp}";
    $paths = [];

    foreach ($request->file('images') as $image) {
        $path = $image->store($folder, 'public');
        $paths[] = $path;
    }

    // Notify Flask (running on port 3001)
    try {
        $response = Http::post('http://localhost:3001/upload', [
            'timestamp' => $timestamp
        ]);
        $flaskResponse = $response->json();
    } catch (\Exception $e) {
        $flaskResponse = ['error' => 'Flask server not reachable', 'exception' => $e->getMessage()];
    }

    return response()->json([
        'message' => 'Images uploaded.',
        'timestamp' => $timestamp,
        'flask' => $flaskResponse,
    ]);
}

}