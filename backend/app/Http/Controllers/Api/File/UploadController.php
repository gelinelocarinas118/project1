<?php

namespace App\Http\Controllers\api\file;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;
use App\Models\Reconstruction;


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
    
        // Save initial record with images saved
        $model = Reconstruction::create([
            'timestamp' => $timestamp,
            'is_saved' => true,
            'is_processing' => false,
            'is_model_ready' => false,
            'is_failed' => false,
            'message' => 'Images saved in Laravel.'
        ]);
    
        // Notify Flask (running on port 3001)
        try {
            $response = Http::post('http://localhost:3001/upload', [
                'timestamp' => $timestamp
            ]);
    
            if ($response->successful()) {
                $model->update([
                    'is_processing' => true,
                    'message' => 'Processing started by Flask.'
                ]);
    
                return response()->json([
                    'message' => 'Images uploaded and sent to Flask.',
                    'timestamp' => $timestamp,
                    'flask' => $response->json(),
                ]);
            } else {
                return response()->json([
                    'error' => 'Flask upload failed.',
                    'flask' => $response->body(),
                ], 500);
            }
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Flask server not reachable',
                'exception' => $e->getMessage()
            ], 500);
        }
    }
    

}